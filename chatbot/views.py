from django.shortcuts import render
import cohere
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from dotenv import load_dotenv
import os

load_dotenv()

def chatbot_view(request):
    return render(request, 'chatbot/chatbot.html')

COHERE_API_KEY = os.getenv('COHERE_API_KEY')
co = cohere.Client(COHERE_API_KEY)

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_msg = data.get('message')
        selected_hero = data.get('hero')  # This can be None or a string

        # Reset chat memory if "__reset__" message is received
        if user_msg == "__reset__":
            request.session['chat_history'] = []
            return JsonResponse({'response': 'Chat memory has been cleared.'})

        # Initialize chat memory if it doesn't exist
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []

        history = request.session['chat_history']

        # Build past conversation for context (limit to last 6 exchanges)
        context = ""
        for turn in history[-6:]:
            context += f"User: {turn['user']}\n{turn['bot_name']}: {turn['bot']}\n"

        # Choose bot name (character or default)
        bot_name = selected_hero if selected_hero else "Bot"

        # Prompt depends on hero mode
        if selected_hero:
            prompt = (
                f"You are {bot_name}, a superhero with a unique personality. "
                f"Reply as {bot_name} would in character.\n\n"
                f"{context}User: {user_msg}\n{bot_name}:"
            )
        else:
            prompt = (
                f"You are a friendly and helpful chatbot.\n\n"
                f"{context}User: {user_msg}\nBot:"
            )

        # Generate response using Cohere
        response = co.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )

        bot_reply = response.generations[0].text.strip()

        # Append new message to session history
        history.append({
            'user': user_msg,
            'bot': bot_reply,
            'bot_name': bot_name
        })
        request.session['chat_history'] = history

        return JsonResponse({'response': bot_reply})

    return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)
