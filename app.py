from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS # NOVIDADE: Importa a biblioteca CORS

# --- Configuração de Variável de Ambiente ---
# A chave é lida de forma segura do Render, onde você configurou PUSHPAY_API_KEY.
YOUR_PUSHPAY_API_KEY = os.environ.get("PUSHPAY_API_KEY") 

# --- Configuração do Flask ---
app = Flask(__name__)
CORS(app) # NOVIDADE: Habilita o CORS para permitir requisições de outras origens (seu arquivo HTML local)

# --- Rota da API ---
@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    # 1. Verifica se a chave de API foi carregada
    if not YOUR_PUSHPAY_API_KEY:
        return jsonify({"message": "Erro: Chave de API da PushinPay não configurada no ambiente."}), 400

    try:
        # 2. Obtém o valor em centavos do JSON do Front-end
        data = request.get_json()
        valor_em_centavos = data.get('valor_em_centavos')

        if not valor_em_centavos or not isinstance(valor_em_centavos, int) or valor_em_centavos <= 0:
            return jsonify({"message": "Valor em centavos inválido."}), 400

        # 3. Prepara o payload para a API da PushinPay
        payload = {
            "amount": valor_em_centavos,
            "description": "Pagamento de Assinatura Streaming",
            # Outros parâmetros como CPF/CNPJ, etc., podem ser adicionados aqui se necessário.
        }

        # 4. Envia a requisição para a PushinPay
        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json"
        }
        
        # URL da API de geração de PIX da PushinPay (confirme esta URL com a documentação)
        pushpay_api_url = "https://api.pushinpay.com/v1/pix/qrcode" 
        
        response = requests.post(pushpay_api_url, headers=headers, json=payload)
        response.raise_for_status() # Lança um erro para status 4xx/5xx

        pushpay_data = response.json()
        
        # 5. Extrai os dados essenciais
        pix_code = pushpay_data.get('pix_code')
        qrcode_url = pushpay_data.get('qrcode_url')

        if not pix_code or not qrcode_url:
             return jsonify({
                "message": "Resposta da PushinPay incompleta.",
                "details": pushpay_data
            }), 500

        # 6. Retorna os dados para o Front-end
        return jsonify({
            "qrcode_url": qrcode_url,
            "pix_code": pix_code,
            "message": "PIX gerado com sucesso."
        })

    except requests.exceptions.HTTPError as err:
        # Erros da API (ex: chave inválida, dados mal formatados)
        try:
            error_details = err.response.json()
            error_message = error_details.get('message', 'Erro desconhecido na API da PushinPay.')
        except:
            error_message = f"Erro HTTP: {err.response.status_code} - {err.response.text}"
            
        return jsonify({"message": "Erro ao gerar PIX na PushinPay.", "details": error_message}), err.response.status_code
        
    except Exception as e:
        # Outros erros de servidor
        return jsonify({"message": "Erro interno do servidor.", "details": str(e)}), 500

# --- Ponto de Entrada Principal ---
if __name__ == '__main__':
    # Esta parte só roda localmente
    app.run(debug=True)