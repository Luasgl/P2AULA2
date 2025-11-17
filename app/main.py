from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import re

app = FastAPI(title="Sistema de Padronização de Nomes e E-mails")

# Configuração do banco de dados SQLite
SQLALHCHEMY_DATABASE_URL = "sqlite:///./usuarios.db"
engine = create_engine(SQLALHCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine )
Base = declarative_base()

# Modelo SQLAlchemy para o banco de dados
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String, unique=True, index=True)

#Criação de tabelas
##Se não existir tabela, ele criará
Base.metadata.create_all(bind=engine)

#Modelo Pydantic para validação de dados
##JSON da API que alimenta base de dados
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr

#Função para padronizar nome
def padronizar_nome(nome: str) -> str:
     #typehint dica (não imposição do tipo) de que a variável é uma string
     nome = " ".join(nome.split()).lower() #remove espaços e transformar em letra minúscula

     #Capitaliza cada palavra
     nome = nome.title()

     #Tratamento para nomes com "da", "de", "do", "dos", "das"
     preposicoes = ['Da', 'De', 'Do', 'Dos', 'Das']
     palavras = nome.split()
     nome_final = []

     for palavra in palavras:
         if palavra in preposicoes:
             nome_final.append(palavra.lower())

         else:
             nome_final.append(palavra)
             
             return " ".join(nome_final)
        
#Função para padronizar e-mail   
def padroniza_email(nome: str) ->str:
    #Remove acentos
    from unicodedata import normalize
    email = nome.lower().replace(' ', '.')

    #Remove caracteres especiais
    email = re.sub(r'[^a-z0-9.]','', email)

    #Remove pontos duplicados
    email = re.sub(r'\.+', '.', email)

    #Remove ponto no inicio ou fim
    email = email.strip('.')

    return f'{email}@empresa.com.br'

#Fazendo um POST - criando um registro na API
#Fazer um GET - Lendo registro da API
#CRUD - Acrônimo para as quatro operações básicas de manipulação
#de dados: Create, Read, Update, Delete

@app.post("/usuarios/")
async def criar_usuario(usuario: UsuarioBase):
    nome_padronizado = padronizar_nome(usuario.nome)
    email_padronizado = padroniza_email(nome_padronizado)

    db = SessionLocal()
    try:
        novo_usuario = Usuario(nome=nome_padronizado, email=email_padronizado)
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        return {
            "id": novo_usuario.id,
            "nome": novo_usuario.nome,
            "e-mail": novo_usuario.email,
            "detalhes": {
                "Nome_original": usuario.nome,
                "nome_padronizado": nome_padronizado,
                "email_gerado": email_padronizado
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.get("/usuarios")
async def listar_usuarios():
    db = SessionLocal()
    try:
        usuarios = db.query(Usuario).all()
        return usuarios
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Bem-vindo! O servidor está funcionando!"}