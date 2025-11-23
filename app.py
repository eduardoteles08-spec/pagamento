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
    # 1. Verifica se a chave de API foi carregada
    if not YOUR_PUSHPAY_API_KEY:
        print("ERRO: Chave PUSHPAY_API_KEY não carregada.")
        return jsonify({"message": "Erro de configuração: Chave de API não encontrada no servidor."}), 500

    try:
        # 2. Obtém o valor em Reais (R$) do JSON do Front-end (campo 'value')
        data = request.get_json()
        valor_em_reais = data.get('value')

        if not valor_em_reais or not isinstance(valor_em_reais, (int, float)) or valor_em_reais <= 0.50:
            # ⚠️ Se este erro aparecer, significa que o Front-end não está enviando 'value' corretamente.
            return jsonify({"message": "Valor para PIX inválido ou abaixo do mínimo permitido."}), 400

        # 3. CONVERSÃO PARA CENTAVOS: Se a PushinPay requer centavos (ex: 49.90 -> 4990)
        valor_em_centavos = int(round(valor_em_reais * 100))
        
        # 4. Prepara o payload para a API da PushinPay
        payload = {
            # O endpoint cashIn usa o campo 'value', mas espera o valor em centavos.
            "value": valor_em_centavos, 
            "webhook_url": "https://seu-site.com/webhook", 
            "split_rules": [],
            "description": "Pagamento de Assinatura Streaming"
        }

        # 5. Envia a requisição para a PushinPay
        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # ⚠️ URL FINAL CORRIGIDA
        pushpay_api_url = "https://api.pushinpay.com.br/api/pix/cashIn" 
        
        # verify=False corrige o erro de certificado SSL
        response = requests.post(pushpay_api_url, headers=headers, json=payload, verify=False)
        
        # 6. Captura erros da API PushinPay (ex: 401, 400)
        response.raise_for_status() 

        pushpay_data = response.json()
        
        # 7. Extrai os dados e retorna ao Front-end
        # Os nomes dos campos de retorno (pix_code e qrcode_url) são mantidos, 
        # mas podem precisar de ajuste dependendo da resposta real da PushinPay.
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
        # Lida com erros da PushinPay (Chave errada, valor rejeitado, etc.)
        error_status = err.response.status_code
        error_text = err.response.text
        
        print(f"ERRO API PUSHPAY: Status {error_status}, Resposta: {error_text}")
        
        return jsonify({
            "message": f"Falha na API da PushinPay (Erro {error_status}). Verifique a chave de API e o valor.",
            "details": error_text
        }), error_status
        
    except Exception as e:
        # Captura qualquer outro erro interno (500)
        print(f"ERRO INTERNO GRAVE: {str(e)}")
        return jsonify({"message": "Erro interno do servidor ao processar a requisição.", "details": str(e)}), 500

# --- Ponto de Entrada Principal ---
if __name__ == '__main__':
    app.run(debug=True)