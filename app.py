from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS # Importa a biblioteca CORS

# --- Configuração de Variável de Ambiente ---
# A chave é lida de forma segura da variável de ambiente no Render.
YOUR_PUSHPAY_API_KEY = os.environ.get("PUSHPAY_API_KEY") 

# --- Configuração do Flask ---
app = Flask(__name__)
CORS(app) # Habilita o CORS para permitir requisições de outras origens

# --- Rota da API ---
@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    # 1. Verifica se a chave de API foi carregada corretamente
    if not YOUR_PUSHPAY_API_KEY:
        # Erro de configuração: A variável de ambiente não foi lida
        print("ERRO: Chave PUSHPAY_API_KEY não carregada.")
        return jsonify({"message": "Erro de configuração: Chave de API não encontrada no servidor. (500)"}), 500

    try:
        # 2. Obtém o valor em centavos do JSON do Front-end
        data = request.get_json()
        valor_em_centavos = data.get('valor_em_centavos')

        if not valor_em_centavos or not isinstance(valor_em_centavos, int) or valor_em_centavos <= 0:
            return jsonify({"message": "Valor em centavos inválido na requisição."}), 400

        # 3. Prepara o payload para a API da PushinPay
        payload = {
            "amount": valor_em_centavos,
            "description": "Pagamento de Assinatura Streaming",
        }

        # 4. Envia a requisição para a PushinPay
        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json"
        }
        
        pushpay_api_url = "https://api.pushinpay.com.br/api/v1/pix/qrcode" 
        
        response = requests.post(pushpay_api_url, headers=headers, json=payload, verify=False)
        
        # 5. Captura erros da API PushinPay (como 401, 400, etc.)
        response.raise_for_status() 

        pushpay_data = response.json()
        
        # 6. Extrai os dados e retorna ao Front-end
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
        # Este bloco lida com erros da PushinPay (ex: 401 Unauthorized por chave errada)
        error_status = err.response.status_code
        error_text = err.response.text
        
        print(f"ERRO API PUSHPAY: Status {error_status}, Resposta: {error_text}")
        
        return jsonify({
            "message": f"Falha na API da PushinPay (Erro {error_status}). A chave de API pode estar incorreta ou o valor de PIX inválido.",
            "details": error_text
        }), error_status
        
    except Exception as e:
        # Este bloco captura qualquer outro erro interno (500)
        print(f"ERRO INTERNO GRAVE: {str(e)}")
        return jsonify({"message": "Erro interno do servidor ao processar a requisição.", "details": str(e)}), 500

# --- Ponto de Entrada Principal ---
if __name__ == '__main__':
    app.run(debug=True)