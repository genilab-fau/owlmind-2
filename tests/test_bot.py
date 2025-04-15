##
## OwlMind - Platform for Education and Experimentation with Generative Intelligent Systems
## bot-1.py :: Getting Started with simple HybridAI-based Discord Bot
## 
#  
# Copyright (c) 2024 The Generative Intelligence Lab @ FAU
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# Documentation and Getting Started:
#    https://github.com/genilab-fau/owlmind
#
# Class Documentation at:
#    https://github.com/genilab-fau/owlmind/bot-1.md
#
# Disclaimer: 
# Generative AI has been used extensively while developing this package.
# 

from dotenv import dotenv_values
from owlmind.pipeline import ModelProvider
from owlmind.simple import SimpleEngine
from owlmind.discord import DiscordBot

if __name__ == '__main__':

    # load token from .env
    config = dotenv_values('.env')
    TOKEN = config['DISCORD_TOKEN']
    URL = config['SERVER_URL']
    MODEL = config['SERVER_MODEL'] if 'SERVER_MODEL' in config else None
    TYPE = config['SERVER_TYPE'] if 'SERVER_TYPE' in config else None
    API_KEY = config['SERVER_API_KEY'] if 'SERVER_API_KEY' in config else None

    # Configure a ModelProvider if there is an URL
    provider = ModelProvider(type=TYPE,  base_url=URL, api_key=API_KEY, model=MODEL) if URL else None

    # Load Simples Bot Brain loading rules from a CSV
    engine = SimpleEngine(id='bot-1')
    engine.model_provider = provider
    engine.load('rules/bot-rules-3.csv')

    # Kick start the Bot Runner process
    bot = DiscordBot(token=TOKEN, engine=engine, debug=True)
    bot.run()

