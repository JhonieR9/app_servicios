import requests
import json

# Probar el endpoint de listar registros
print("=" * 60)
print("PROBANDO ENDPOINT: /trabajador/registros/listar")
print("=" * 60)

try:
    response = requests.get("http://localhost:8000/trabajador/registros/listar")
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Respuesta exitosa")
        print(f"Número de registros: {len(data.get('registros', []))}")
        
        if data.get('registros'):
            print("\nPrimer registro:")
            print(json.dumps(data['registros'][0], indent=2, ensure_ascii=False))
        else:
            print("\n❌ El array de registros está vacío")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: No se puede conectar al servidor")
    print("Asegúrate de que el servidor esté corriendo con:")
    print("uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
except Exception as e:
    print(f"\n❌ Error: {e}")
