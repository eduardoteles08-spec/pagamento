# app.py (Seu Servidor Back-end em Python/Flask)
from flask import Flask, request, jsonify
import requests

# ⚠️ 1. ONDE COLOCAR SUA CHAVE DE API (SECRETA) ⚠️
# TROQUE A CHAVE ABAIXO PELA SUA CHAVE REAL DA PUSHPAY
YOUR_PUSHPAY_API_KEY = "SUA_CHAVE_SECRETA_DA_PUSHPAY_AQUI"

# Inicializa o Flask
app = Flask(__name__)

# Rota que receberá a requisição do seu JavaScript (Front-end)
@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    # Verifica se a chave foi configurada
    if YOUR_PUSHPAY_API_KEY == "SUA_CHAVE_SECRETA_DA_PUSHPAY_AQUI":
        return jsonify({"message": "Erro: A chave de API da PushinPay não foi configurada."}), 500
        
    try:
        data = request.get_json()
        # O valor é esperado em centavos, conforme enviado pelo Front-end
        valor_em_centavos = data.get('valor_em_centavos')
        
        if valor_em_centavos is None or valor_em_centavos <= 0:
            return jsonify({"message": "Valor inválido recebido."}), 400

        # --- PREPARAÇÃO DA CHAMADA SEGURA PARA A API DA PUSHPAY ---
        
        # URL do endpoint de geração de PIX da PushinPay (VERIFIQUE COM A DOCUMENTAÇÃO DELES)
        url = "https://api.pushinpay.com/v1/pix/gerar" 
        
        headers = {
            # Sua chave fica segura aqui, invisível ao navegador do cliente
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": valor_em_centavos, 
            "description": "Pagamento de Assinatura",
            # Adicione outros campos, como client_id, se a PushinPay exigir
        }
        
        # Faz a chamada POST
        response = requests.post(url, json=payload, headers=headers)
        
        # --- TRATAMENTO DA RESPOSTA ---
        if response.status_code in [200, 201]:
            pix_data = response.json()
            
            # Mapeia a resposta real da PushinPay para o Front-end
            resultado = {
                # O nome dos campos DEVE coincidir com o que a PushinPay retorna
                "qrcode_url": pix_data.get('qrcode_image_url'), 
                "pix_code": pix_data.get('pix_br_code'),         
                "success": True
            }
            return jsonify(resultado), 200
        else:
            print(f"Erro na API PushinPay: {response.text}")
            return jsonify({
                "message": "Erro ao processar o PIX na PushinPay.",
                "details": response.json() 
            }), response.status_code

    except Exception as e:
        print(f"Erro interno: {e}")
        return jsonify({"message": f"Erro interno do servidor: {str(e)}"}), 500

if __name__ == '__main__':
    # Para testes locais: http://127.0.0.1:5000/
    app.run(debug=True, port=5000)