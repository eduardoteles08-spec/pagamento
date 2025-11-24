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

# URL ATUALIZADA PARA PRODUÇÃO (LIVE)
PUSHINPAY_BASE_URL = "https://api.pushinpay.com.br/api" 

@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    if not YOUR_PUSHPAY_API_KEY:
        print("ERRO: Chave PUSHPAY_API_KEY não carregada.")
        return jsonify({"message": "Erro de configuração: Chave de API não encontrada no servidor."}), 500

    try:
        # 1. Obtém o valor em Reais (R$) do Front-end
        data = request.get_json()
        valor_em_reais = data.get('value')

        if not valor_em_reais or not isinstance(valor_em_reais, (int, float)) or valor_em_reais <= 0.50:
            return jsonify({"message": "Valor para PIX inválido ou abaixo do mínimo permitido."}), 400

        # 2. CONVERSÃO PARA CENTAVOS (R$ 49.90 -> 4990)
        valor_decimal = Decimal(str(valor_em_reais))
        valor_em_centavos = int(valor_decimal.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP) * 100)
        
        # 3. Prepara o payload para a API da PushinPay
        payload = {
            "value": valor_em_centavos, 
            "webhook_url": "https://seu-site.com/webhook", 
            "split_rules": [],
            "description": "Pagamento de Assinatura Streaming"
        }

        # 4. Envia a requisição para a PushinPay
        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        pushpay_api_url = f"{PUSHINPAY_BASE_URL}/pix/cashIn" 
        
        # verify=False corrige o erro de certificado SSL
        response = requests.post(pushpay_api_url, headers=headers, json=payload, verify=False)
        
        # 5. Lança erro se o status for 4xx ou 5xx
        response.raise_for_status() 

        pushpay_data = response.json()
        
        # 6. 🟢 CORREÇÃO DE EXIBIÇÃO: Mapeamento dos campos corretos
        # O Front-end espera estes nomes: 'qrcode_url' e 'pix_code'
        pix_code = pushpay_data.get('qr_code')       # Pega o Copia e Cola da PushinPay
        qrcode_url = pushpay_data.get('qr_code_base64') # Pega a Imagem Base64 da PushinPay

        if not pix_code or not qrcode_url:
             # Este erro só deve ocorrer se a PushinPay enviar um JSON de sucesso incompleto.
             return jsonify({
                "message": "Resposta da PushinPay incompleta. Dados PIX faltando.",
                "details": pushpay_data
            }), 500

        return jsonify({
            "qrcode_url": qrcode_url, 
            "pix_code": pix_code,
            "message": "PIX gerado com sucesso."
        })

    except requests.exceptions.HTTPError as err:
        error_status = err.response.status_code
        error_text = err.response.text
        
        print(f"ERRO API PUSHPAY: Status {error_status}, Resposta: {error_text}")
        
        # Retorna o erro capturado (ex: 401 ou 422) para o Front-end
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