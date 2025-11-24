from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS 
from decimal import Decimal, ROUND_HALF_UP

# --- Configuração de Variável de Ambiente ---
YOUR_PUSHPAY_API_KEY = os.environ.get("PUSHPAY_API_KEY") 

# --- Configuração do Flask ---
app = Flask(__name__)
CORS(app) 

# URL ATUALIZADA PARA PRODUÇÃO (Se a sua chave for de Produção)
PUSHINPAY_BASE_URL = "https://api.pushinpay.com.br/api" 

@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    if not YOUR_PUSHPAY_API_KEY:
        print("ERRO: Chave PUSHPAY_API_KEY não carregada.")
        return jsonify({"message": "Erro de configuração: Chave de API não encontrada no servidor."}), 500

    try:
        data = request.get_json()
        valor_em_reais = data.get('value')

        if not valor_em_reais or not isinstance(valor_em_reais, (int, float)) or valor_em_reais <= 0.50:
            return jsonify({"message": "Valor para PIX inválido ou abaixo do mínimo permitido."}), 400

        # CONVERSÃO PARA CENTAVOS (R$ 49.90 -> 4990)
        valor_decimal = Decimal(str(valor_em_reais))
        valor_em_centavos = int(valor_decimal.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP) * 100)
        
        payload = {
            "value": valor_em_centavos, 
            "webhook_url": "https://seu-site.com/webhook", 
            "split_rules": [],
            "description": "Pagamento de Assinatura Streaming"
        }

        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        pushpay_api_url = f"{PUSHINPAY_BASE_URL}/pix/cashIn" 
        
        response = requests.post(pushpay_api_url, headers=headers, json=payload, verify=False)
        
        # Se a requisição foi bem-sucedida, o status 200/201 é retornado.
        response.raise_for_status() 

        pushpay_data = response.json()
        
        # 🟢 CORREÇÃO CRÍTICA: Mapear os campos corretos da PushinPay para a sua tela
        pix_code = pushpay_data.get('qr_code')  # PushinPay usa 'qr_code' para o Copia e Cola
        qrcode_url = pushpay_data.get('qr_code_base64') # PushinPay usa 'qr_code_base64' para a imagem

        if not pix_code or not qrcode_url:
             return jsonify({
                "message": "Resposta da PushinPay incompleta. Dados PIX faltando.",
                "details": pushpay_data
            }), 500

        # O Front-end espera estes nomes: 'qrcode_url' e 'pix_code'
        return jsonify({
            "qrcode_url": qrcode_url, 
            "pix_code": pix_code,
            "message": "PIX gerado com sucesso."
        })

    except requests.exceptions.HTTPError as err:
        error_status = err.response.status_code
        error_text = err.response.text
        
        print(f"ERRO API PUSHPAY: Status {error_status}, Resposta: {error_text}")
        
        # Se o pagamento foi criado na PushinPay, mas o log mostra 401/422,
        # significa que a chamada atual está falhando.
        return jsonify({
            "message": f"Falha na API da PushinPay (Erro {error_status}). Verifique a chave de API e o valor. Detalhes: {error_text}",
            "details": error_text
        }), error_status
        
    except Exception as e:
        print(f"ERRO INTERNO GRAVE: {str(e)}")
        return jsonify({"message": "Erro interno do servidor ao processar a requisição.", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)