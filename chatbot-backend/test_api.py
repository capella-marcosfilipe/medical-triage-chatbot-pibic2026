#!/usr/bin/env python3
"""Test script to demonstrate the API workflow."""
import requests
import json
import time

BASE_URL = "http://localhost:8001/api/v1"


def print_response(response, description):
    """Print a formatted API response."""
    print(f"\n{'=' * 60}")
    print(f"TEST: {description}")
    print(f"{'=' * 60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_workflow():
    """Test the complete medical triage workflow."""
    
    print("\n🏥 Medical Triage Chatbot - API Workflow Test")
    print("=" * 60)
    
    # Step 1: Initialize patient session
    print("\n📋 Step 1: Initializing patient session...")
    paciente_data = {
        "nome_completo": "João da Silva",
        "endereco": "Rua das Flores, 123, Recife-PE",
        "idade": 35
    }
    
    response = requests.post(f"{BASE_URL}/iniciar_atendimento", json=paciente_data)
    print_response(response, "POST /iniciar_atendimento")
    
    if response.status_code != 200:
        print("❌ Failed to initialize session. Exiting.")
        return
    
    session_id = response.json()["session_id"]
    print(f"\n✅ Session created successfully! Session ID: {session_id}")
    
    # Step 2: Get smartwatch data
    print("\n⌚ Step 2: Retrieving smartwatch data...")
    time.sleep(1)
    
    response = requests.get(f"{BASE_URL}/obter_dados_smartwatch/{session_id}")
    print_response(response, "GET /obter_dados_smartwatch")
    
    if response.status_code != 200:
        print("❌ Failed to get smartwatch data. Exiting.")
        return
    
    print("\n✅ Smartwatch data retrieved successfully!")
    
    # Step 3: Simulate chat interaction
    print("\n💬 Step 3: Simulating chat with AI...")
    time.sleep(1)
    
    user_messages = [
        "Estou com febre há 2 dias e dor de cabeça forte",
        "A febre está em torno de 38.5°C",
        "Não tenho alergias conhecidas",
        "Não estou tomando nenhum medicamento"
    ]
    
    for msg in user_messages:
        chat_data = {
            "session_id": session_id,
            "user_message": msg
        }
        
        response = requests.post(f"{BASE_URL}/chat_with_gemini", json=chat_data)
        print_response(response, f"POST /chat_with_gemini - User: {msg[:30]}...")
        
        if response.status_code != 200:
            print(f"❌ Failed to send message. Exiting.")
            return
        
        response_data = response.json()
        if response_data.get("status") == "final":
            print("\n✅ Conversation finalized!")
            print("\n📄 Medical Record Generated:")
            print(json.dumps(response_data.get("ficha_de_atendimento"), indent=2, ensure_ascii=False))
            break
        
        time.sleep(1)
    
    # Step 4: Get complete medical record
    print("\n📄 Step 4: Retrieving complete medical record...")
    time.sleep(1)
    
    response = requests.get(f"{BASE_URL}/obter_ficha_completa/{session_id}")
    print_response(response, "GET /obter_ficha_completa")
    
    if response.status_code == 200:
        print("\n✅ Medical record retrieved successfully!")
    else:
        print("\n❌ Failed to retrieve medical record.")
    
    print("\n" + "=" * 60)
    print("🎉 Workflow test completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        # Check if server is running
        health_url = BASE_URL.replace("/api/v1", "") + "/health"
        response = requests.get(health_url, timeout=2)
        if response.status_code != 200:
            print("❌ Server is not responding correctly.")
            exit(1)
    except requests.exceptions.ConnectionError:
        server_url = BASE_URL.replace("/api/v1", "")
        print(f"❌ Server is not running on {server_url}")
        print("Please start the server with: python main.py")
        exit(1)
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        exit(1)
    
    test_workflow()
