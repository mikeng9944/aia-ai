#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import json
import logging
import os
import sys
import time
from pathlib import Path
import streamlit as st
import requests

logging.basicConfig(stream=sys.stdout, level=logging.INFO,  # set to logging.DEBUG for verbose output
        format="[%(asctime)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
logger = logging.getLogger(__name__)

# Your Speech resource key and region
# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"

SUBSCRIPTION_KEY = os.getenv("SUBSCRIPTION_KEY", '126711816c574abfb5f9879bdd51d7ff')
SERVICE_REGION = os.getenv("SERVICE_REGION", "westeurope")

NAME = "Simple avatar synthesis"
DESCRIPTION = "Simple avatar synthesis description"

# The service host suffix.
SERVICE_HOST = "customvoice.api.speech.microsoft.com"


def submit_synthesis(user_input):
    url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar'
    header = {
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
        'Content-Type': 'application/json'
    }

    payload = {
        'displayName': NAME,
        'description': DESCRIPTION,
        "textType": "PlainText",
        'synthesisConfig': {
            "voice": "en-US-JennyNeural",
        },
        # Replace with your custom voice name and deployment ID if you want to use custom voice.
        # Multiple voices are supported, the mixture of custom voices and platform voices is allowed.
        # Invalid voice name or deployment ID will be rejected.
        'customVoices': {
            # "YOUR_CUSTOM_VOICE_NAME": "YOUR_CUSTOM_VOICE_ID"
        },
        "inputs": [
            {
                "text": user_input,  # Use user input here
            },
        ],
        "properties": {
            "customized": False, # set to True if you want to use customized avatar
            "talkingAvatarCharacter": "lisa",  # talking avatar character
            "talkingAvatarStyle": "technical-sitting",  # talking avatar style, required for prebuilt avatar, optional for custom avatar
            "videoFormat": "webm",  # mp4 or webm, webm is required for transparent background
            "videoCodec": "vp9",  # hevc, h264 or vp9, vp9 is required for transparent background; default is hevc
            "subtitleType": "soft_embedded",
            "backgroundColor": "transparent",
        }
    }

    response = requests.post(url, json.dumps(payload), headers=header)
    if response.status_code < 400:
        logger.info('Batch avatar synthesis job submitted successfully')
        logger.info(f'Job ID: {response.json()["id"]}')
        return response.json()["id"]
    else:
        logger.error(f'Failed to submit batch avatar synthesis job: {response.text}')


def get_synthesis(job_id):
    url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar/{job_id}'
    header = {
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY
    }
    response = requests.get(url, headers=header)
    if response.status_code < 400:
        logger.debug('Get batch synthesis job successfully')
        logger.debug(response.json())
    if response.json()['status'] == 'Succeeded':
        logger.info(f'Batch synthesis job succeeded, download URL: {response.json()["outputs"]["result"]}')
        return response.json()['status'], response.json()["outputs"]["result"]
    else:
        return response.json()['status'], None
  
def list_synthesis_jobs(skip: int = 0, top: int = 100):
    """List all batch synthesis jobs in the subscription"""
    url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar?skip={skip}&top={top}'
    header = {
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY
    }
    response = requests.get(url, headers=header)
    if response.status_code < 400:
        logger.info(f'List batch synthesis jobs successfully, got {len(response.json()["values"])} jobs')
        logger.info(response.json())
    else:
        logger.error(f'Failed to list batch synthesis jobs: {response.text}')
  
  
def main():
    st.title("GTI x AZURE text to avater synthesis demo")

    # Get user input from Streamlit
    user_input = st.text_input("Enter the text you want to convert to voice:")

    if st.button('Submit'):
        job_id = submit_synthesis(user_input)
        if job_id is not None:
            while True:
                status = get_synthesis(job_id)
                if status == 'Succeeded':
                    st.success('Batch avatar synthesis job succeeded')
                    break
                elif status == 'Failed':
                    st.error('Batch avatar synthesis job failed')
                    break
                else:
                    st.info(f'Batch avatar synthesis job is still running, status [{status}]')
                    time.sleep(5)

if __name__ == '__main__':
    user_input = st.text_input("Enter the text to generate voice speech")
    if user_input:
        job_id = submit_synthesis(user_input)
        if job_id is not None:
            while True:
                status, download_url = get_synthesis(job_id)
                if status == 'Succeeded':
                    st.markdown(f'[Hi your ai avater is ready, click here to download]({download_url})')
                    break  # Exit the loop
                elif status == 'Failed':
                    st.error('Batch avatar synthesis job failed')
                    break  # Exit the loop
                else:
                    time.sleep(5)