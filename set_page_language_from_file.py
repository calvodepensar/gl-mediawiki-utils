#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    set_page_language_from_file.py

    This script reads a list of MediaWiki page titles from a text file
    (one title per line), logs into a MediaWiki site, and sets the
    language of each page to a specified language code.

    Code is inspired in MediaWiki API demos; thanks!

    MIT License
"""

import requests
import sys

# --- Configuration ---
# The URL to the api.php endpoint of your MediaWiki site.
WIKI_URL = "https://your.site.com/w/api.php"
# The language code to set the pages to (e.g., 'es' for Spanish).
TARGET_LANG = "es"
# The name of the file containing the list of page titles, one per line.
PAGES_FILE = "pages.txt"
# Your bot credentials.
# IMPORTANT: Obtain these from Special:BotPasswords on your wiki.
# https://www.mediawiki.org/wiki/Special:BotPasswords
BOT_USER_NAME = "bot_user_name"
BOT_PASSWORD = "bot_password"
# --- End of Configuration ---

def main():
    """Main function to execute the script logic."""
    session = requests.Session()

    # Step 1: Log in and get the CSRF token
    try:
        csrf_token = login_and_get_csrf_token(session)
        print("✅ Successfully logged in and obtained CSRF token.")
    except Exception as e:
        print(f"❌ Error during login: {e}")
        sys.exit(1) # Exit if login fails

    # Step 2: Read page titles from the specified file
    try:
        with open(PAGES_FILE, 'r', encoding='utf-8') as f:
            # Read lines and strip whitespace/newlines from each
            page_titles = [line.strip() for line in f if line.strip()]
        print(f"ℹ️  Found {len(page_titles)} page titles in '{PAGES_FILE}'.")
    except FileNotFoundError:
        print(f"❌ Error: The file '{PAGES_FILE}' was not found.")
        print("Please create this file and add one page title per line.")
        sys.exit(1)

    # Step 3: Iterate through each page title and set its language
    for title in page_titles:
        print(f"\nProcessing page: '{title}'...")
        set_page_language(session, title, csrf_token)

    print("\n✅ Script finished.")

def login_and_get_csrf_token(session):
    """Handles the login process and fetches the CSRF token."""
    # First, get a login token
    login_token_params = {
        "action": "query",
        "meta": "tokens",
        "type": "login",
        "format": "json"
    }
    response = session.get(url=WIKI_URL, params=login_token_params)
    response.raise_for_status() # Raise an exception for bad status codes
    data = response.json()
    login_token = data['query']['tokens']['logintoken']

    # Now, log in using the bot credentials and the login token
    login_params = {
        "action": "login",
        "lgname": BOT_USER_NAME,
        "lgpassword": BOT_PASSWORD,
        "lgtoken": login_token,
        "format": "json"
    }
    response = session.post(WIKI_URL, data=login_params)
    response.raise_for_status()
    # Check if login was successful
    login_data = response.json()
    if login_data.get('login', {}).get('result') != 'Success':
        raise Exception(f"Login failed: {login_data.get('login', {}).get('reason', 'Unknown reason')}")

    # Finally, get the CSRF token needed for editing/actions
    csrf_token_params = {
        "action": "query",
        "meta": "tokens",
        "format": "json" # The token type defaults to 'csrf'
    }
    response = session.get(url=WIKI_URL, params=csrf_token_params)
    response.raise_for_status()
    data = response.json()
    return data['query']['tokens']['csrftoken']

def set_page_language(session, page_title, csrf_token):
    """Sends a POST request to change the language of a single page."""
    params = {
        "action": "setpagelanguage",
        "title": page_title,       # Use 'title' instead of 'pageid'
        "token": csrf_token,
        "format": "json",
        "lang": TARGET_LANG        # Use the configured language
    }

    try:
        response = session.post(WIKI_URL, data=params)
        response.raise_for_status()
        data = response.json()

        # Check for errors in the API response
        if 'error' in data:
            print(f"    ❌ API Error: {data['error']['info']}")
        elif 'setpagelanguage' in data:
            # The API returns the language it was set from and to.
            # The 'from' key is only present if a language was already set.
            result = data['setpagelanguage']
            # Use .get() to safely access the 'from' key and provide a default value.
            from_lang = result.get('from', '[not previously set]')
            to_lang = result.get('to', TARGET_LANG)
            print(f"    ✅ Success! Language set to '{to_lang}'. (Previous: {from_lang})")
        else:
            print(f"    ⚠️  Warning: Unknown response format. Full response: {data}")

    except requests.exceptions.RequestException as e:
        print(f"    ❌ HTTP Request Error: {e}")

if __name__ == "__main__":
    # Check if bot credentials have been changed from the default
    if BOT_USER_NAME == "bot_user_name" or BOT_PASSWORD == "bot_password":
        print("⚠️  Warning: Please update the BOT_USER_NAME and BOT_PASSWORD variables in the script.")
    else:
        main()
