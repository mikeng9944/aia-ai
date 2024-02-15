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

SUBSCRIPTION_KEY = os.getenv("SUBSCRIPTION_KEY", '126711816c574abfb5f9879bdd51d7ff')   #speech studio resources group key
SERVICE_REGION = os.getenv("SERVICE_REGION", "westeurope") #resources group location

NAME = "Simple avatar synthesis"
DESCRIPTION = "Simple avatar synthesis description"

# The service host suffix.
SERVICE_HOST = "customvoice.api.speech.microsoft.com"


def submit_synthesis(user_input, voice_option, avatar_style_option):
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
        "voice": voice_option,  # Use voice_option here

        },

        'customVoices': {
            # "YOUR_CUSTOM_VOICE_NAME": "YOUR_CUSTOM_VOICE_ID"(use for customer model)
        },
        "inputs": [
            {
                "text": user_input,  # input
            },
        ],
        "properties": {
            "customized": False, # set to True if you want to use customized avatar
            "talkingAvatarCharacter": "lisa",  # change the model image
            "talkingAvatarStyle": avatar_style_option,  # Use avatar_style_option here
            "videoFormat": "webm",  # mp4 or webm, webm is required for transparent background
            "videoCodec": "vp9",  # hevc, h264 or vp9, vp9 is required for transparent background; default is hevc
            "subtitleType": "soft_embedded",
            "backgroundColor": "transparent",
            "handMovements": "auto"  # Add hand movements here
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
    try:
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            response_json = response.json()
            logger.debug('Get batch synthesis job successfully')
            logger.debug(response_json)
            if response_json['status'] == 'Succeeded':
                download_url = response_json["outputs"]["result"]
                logger.info(f'Batch synthesis job succeeded, download URL: {download_url}')
                return download_url
            else:
                logger.info(f'Job status is not succeeded yet, current status: {response_json["status"]}')
                return None  # Return None to indicate the job hasn't succeeded yet
        else:
            logger.error(f'Failed to get batch synthesis job: {response.text}')
            return None
    except Exception as e:
        logger.error(f'An error occurred while fetching the synthesis job status: {e}')
        return None

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

    def your_function_name():
        url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar'
    # ... (other code)
        response = some_function_that_triggers_the_job()  # Replace with your actual function
    if response.status_code == 200:  # Replace with your actual condition for job success
        download_url = response.json().get('downloadUrl')  # Replace with the actual key for the download URL
        download_file(download_url)
  
    def download_file(url):
        local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
        return local_filename
  
def main():
    st.set_page_config(page_title="GTI x AZURE text to avatar synthesis demo", page_icon=":microphone:")

    # Initialize job_id with None
    job_id = None

    # Get user input from Streamlit
    user_input = st.text_input("Enter the text you want to convert to voice:")
    voice_option = st.selectbox("Choose a voice:", ["en-US-JennyNeural", "zh-HK-HiuGaaiNeural", "en-US-GuyNeural", "en-US-AriaNeural"])
    avatar_style_option = st.selectbox("Choose an avatar style:", ["graceful-sitting", "casual-standing", "professional-standing"])

    # Use a unique key for the button to prevent conflicts
    if st.button('Submit', key='submit_synthesis'):
        job_id = submit_synthesis(user_input, voice_option, avatar_style_option)

    # Check if job_id is not None to ensure it has been assigned
    if job_id is not None:
       while True:
        download_url = get_synthesis(job_id)
        if download_url:
            st.success(f'Batch avatar synthesis job succeeded. Download URL: {download_url}')
            st.markdown(f'[Download synthesized avatar video]({download_url})', unsafe_allow_html=True)
            break
        else:
            # Handle the case where the job is not ready or failed
            st.info('Checking job status, please wait...')
            time.sleep(10)  # Adjust the sleep time as necessary


# Ensures the script can be run standalone
if __name__ == "__main__":
    main()


