from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS 

# --- Configuração de Variável de Ambiente ---
YOUR_PUSHPAY_API_KEY = os.environ.get("PUSHPAY_API_KEY") 

# --- Configuração do Flask ---
app = Flask(__name__)
CORS(app) 

# --- Rota da API ---
@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    if not YOUR_PUSHPAY_API_KEY:
        print("ERRO: Chave PUSHPAY_API_KEY não carregada.")
        return jsonify({"message": "Erro de configuração: Chave de API não encontrada."}), 500

    try:
        # 1. Obtém o valor em Reais (R$) do JSON do Front-end (campo 'value')
        data = request.get_json()
        valor_em_reais = data.get('value')

        if not valor_em_reais or not isinstance(valor_em_reais, (int, float)) or valor_em_reais <= 0.50:
            return jsonify({"message": "Valor para PIX inválido ou abaixo do mínimo permitido."}), 400

        # 2. Prepara o payload com o valor em Reais (float)
        # ASSUMINDO que a PushinPay quer o valor em Reais (ex: 49.90) devido ao erro 'mínimo 5'.
        payload = {
            "value": valor_em_reais, 
            "webhook_url": "https://seu-site.com/webhook", 
            "split_rules": [],
            "description": "Pagamento de Assinatura Streaming"
        }

        # 3. Envia a requisição
        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        pushpay_api_url = "https://api.pushinpay.com.br/api/pix/cashIn" 
        
        # verify=False corrige o erro de certificado SSL
        response = requests.post(pushpay_api_url, headers=headers, json=payload, verify=False)
        
        # 4. Captura erros (401, 400, 422, etc.)
        response.raise_for_status() 

        pushpay_data = response.json()
        
        # 5. Retorna os dados
        pix_code = pushpay_data.get('pix_code')
        qrcode_url = pushpay_data.get('qrcode_url')

        if not pix_code or not qrcode_url:
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
        
        return jsonify({
            "message": f"Falha na API da PushinPay (Erro {error_status}). Verifique a chave de API e o valor.",
            "details": error_text
        }), error_status
        
    except Exception as e:
        return jsonify({"message": "Erro interno do servidor ao processar a requisição.", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)