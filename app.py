from flask import Flask, render_template, request, redirect, session, flash, url_for
import json, hashlib, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_super_secreta'

ARQUIVO_DADOS = 'inquilinos.json'
ARQUIVO_USUARIOS = 'usuarios.json'

# Função de hash
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Carregar/salvar usuários
def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return {}
    with open(ARQUIVO_USUARIOS, 'r') as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, 'w') as f:
        json.dump(usuarios, f, indent=4)

# Carregar/salvar dados dos inquilinos
def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return {}
    with open(ARQUIVO_DADOS, 'r') as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, 'w') as f:
        json.dump(dados, f, indent=4)


# ------------


# Rota de login


# Rota do menu
@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    usuario = session['usuario']
    return render_template('menu.html', nome=usuario['nome'], nivel=usuario['nivel'])

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# Cadastro de usuário (admin)
@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if 'usuario' not in session or session['usuario']['nivel'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        usuarios = carregar_usuarios()
        nome     = request.form['nome']
        if nome in usuarios:
            flash('Usuário já existe.', 'warning')
        else:
            senha   = request.form['senha']
            palavra = request.form['palavra']
            nivel   = request.form['nivel']
            usuarios[nome] = {
                "senha": hash_senha(senha),
                "palavra_secreta": palavra.lower(),
                "nivel": nivel
            }
            salvar_usuarios(usuarios)
            flash(f"Usuário {nome} cadastrado com sucesso!", 'success')
            return redirect(url_for('menu'))
    return render_template('cadastrar_usuario.html')

# Recuperar senha
@app.route('/recuperar_senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        usuarios = carregar_usuarios()
        nome     = request.form['usuario']
        palavra  = request.form['palavra'].lower()
        nova     = request.form['nova']
        if nome in usuarios and usuarios[nome]["palavra_secreta"] == palavra:
            usuarios[nome]["senha"] = hash_senha(nova)
            salvar_usuarios(usuarios)
            flash("Senha redefinida com sucesso!", "success")
            return redirect(url_for('login'))
        else:
            flash("Informações incorretas.", "danger")
    return render_template('recuperar_senha.html')

# Cadastro de inquilino
@app.route('/cadastrar_inquilino', methods=['GET', 'POST'])
def cadastrar_inquilino():
    if 'usuario' not in session or session['usuario']['nivel'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        dados = carregar_dados()
        nome  = request.form['nome']
        if nome in dados:
            flash("Inquilino já cadastrado.", "warning")
        else:
            dados[nome] = {"pagamentos": {}}
            salvar_dados(dados)
            flash("Inquilino cadastrado com sucesso!", "success")
            return redirect(url_for('menu'))
    return render_template('cadastrar_inquilino.html')

# Registrar pagamento
@app.route('/registrar_pagamento', methods=['GET', 'POST'])
def registrar_pagamento():
    if 'usuario' not in session or session['usuario']['nivel'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        dados = carregar_dados()
        nome  = request.form['nome']
        if nome not in dados:
            flash("Inquilino não encontrado.", "danger")
        else:
            ano     = request.form['ano']
            mes     = request.form['mes'].zfill(2)
            chave   = f"{ano}-{mes}"
            aluguel = float(request.form['aluguel'])
            luz     = float(request.form['luz'])
            dados[nome]["pagamentos"][chave] = {
                "aluguel": aluguel,
                "luz": luz
            }
            salvar_dados(dados)
            flash("Pagamento registrado com sucesso!", "success")
            return redirect(url_for('menu'))
    return render_template('registrar_pagamento.html')

# Verificar pendências
@app.route('/verificar_pendencias', methods=['GET', 'POST'])
def verificar_pendencias():
    pendencias = []
    if request.method == 'POST':
        dados = carregar_dados()
        nome  = request.form['nome']
        ano   = request.form['ano']
        if nome not in dados:
            flash("Inquilino não encontrado.", "danger")
        else:
            for mes in range(1, 13):
                chave = f"{ano}-{str(mes).zfill(2)}"
                if chave not in dados[nome]["pagamentos"]:
                    pendencias.append(f"Mês {mes}: PENDENTE")
                else:
                    pendencias.append(f"Mês {mes}: OK")
    return render_template('verificar_pendencias.html', pendencias=pendencias)

# Relatório de pagamentos
@app.route('/relatorio', methods=['GET', 'POST'])
def gerar_relatorio():
    relatorio     = []
    total_aluguel = 0
    total_luz     = 0
    if request.method == 'POST':
        dados = carregar_dados()
        nome  = request.form['nome']
        ano   = request.form['ano']
        if nome not in dados:
            flash("Inquilino não encontrado.", "danger")
        else:
            for mes in range(1, 13):
                chave = f"{ano}-{str(mes).zfill(2)}"
                pagamento = dados[nome]["pagamentos"].get(chave)
                if pagamento:
                    aluguel = pagamento["aluguel"]
                    luz = pagamento["luz"]
                    total_aluguel += aluguel
                    total_luz += luz
                    relatorio.append(f"Mês {mes}: Aluguel R$ {aluguel:.2f}, Luz R$ {luz:.2f}")
                else:
                    relatorio.append(f"Mês {mes}: Sem pagamento")
    return render_template('relatorio.html', relatorio=relatorio,
                           total_aluguel=f"{total_aluguel:.2f}", total_luz=f"{total_luz:.2f}")

# Trocar senha logado
@app.route('/trocar_senha', methods=['GET', 'POST'])
def trocar_senha():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        usuarios = carregar_usuarios()
        nome     = session['usuario']['nome']
        atual    = request.form['atual']
        nova     = request.form['nova']
        if usuarios[nome]["senha"] == hash_senha(atual):
            usuarios[nome]["senha"] = hash_senha(nova)
            salvar_usuarios(usuarios)
            flash("Senha alterada com sucesso.", "success")
            return redirect(url_for('menu'))
        else:
            flash("Senha atual incorreta.", "danger")
    return render_template('trocar_senha.html')

# Início do app
if __name__ == '__main__':
    if not os.path.exists(ARQUIVO_USUARIOS):
        print("Nenhum usuário encontrado. Criando primeiro administrador...")
        nome     = input("Usuário: ")
        senha    = input("Senha: ")
        palavra  = input("Palavra secreta: ")
        usuarios = {
            nome: {
                "senha": hash_senha(senha),
                "palavra_secreta": palavra.lower(),
                "nivel": "admin"
            }
        }
        salvar_usuarios(usuarios)
        print("Usuário administrador criado com sucesso.")
    app.run(debug=True)
