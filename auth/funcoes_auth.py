from db import supabase
import bcrypt

def autenticar_usuario(email, senha_digitada):
    res = supabase.table("usuarios").select("*").eq("email", email).execute()

    if res.data:
        usuario = res.data[0]
        senha_hash = usuario["senha"].encode('utf-8')
        if bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash):
            return usuario
    return None

def cadastrar_novo_usuario(supabase, nome, cargo, email, senha):
    try:
        # Criptografa a senha
        hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 1. Cria o usuário com e-mail e senha
        response = supabase.auth.sign_up({
            "email": email,
            "password": senha
        })

        # Verifica se houve erro na criação do auth
        if response.user is None:  # Verifica se o usuário não foi criado
            return False, f"Erro ao criar usuário: {response.message}"

        user_id = response.user.id  # Acessando o ID do usuário

        # 2. Salva dados adicionais na tabela "usuarios"
        dados_usuario = {
            "id": user_id,     # usa o mesmo ID do auth
            "nome_usuario": nome,
            "cargo": cargo,
            "email": email,
            "senha": hashed_password
        }
        try:
            supabase.table("usuarios").insert(dados_usuario).execute()
            return True, "Usuário cadastrado com sucesso!"
        except Exception as e: 
            return False, f"Erro ao salvar dados do usuário: {e}"

    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"
    
