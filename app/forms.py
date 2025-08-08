from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, BooleanField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from datetime import datetime


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password', message='Senhas não conferem')])
    phone_e164 = StringField('WhatsApp (E.164)', validators=[Regexp(r'^\+?\d{10,15}$', message='Informe telefone em formato internacional E.164'), Length(max=20)])
    submit = SubmitField('Criar Conta')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar link de redefinição')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('password', message='Senhas não conferem')])
    submit = SubmitField('Redefinir Senha')


class TicketForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Descrição')
    status = SelectField('Status', choices=[
        ('aberto','Aberto'),
        ('pendente_totvs','Pendente TOTVS'),
        ('pendente_feso','Pendente FESO'),
        ('validacao_cliente','Validação Cliente'),
        ('fechado','Fechado')
    ])
    priority = SelectField('Prioridade', choices=[('baixa','Baixa'),('media','Média'),('alta','Alta'),('critica','Crítica')])
    vendor = StringField('Terceirizada', validators=[Length(max=120)])
    assignee = StringField('Responsável', validators=[Length(max=120)])
    submit = SubmitField('Salvar')


class InteractionForm(FlaskForm):
    content = TextAreaField('Conteúdo', validators=[DataRequired()])
    author = StringField('Autor', validators=[DataRequired(), Length(max=120)])
    created_at = DateTimeLocalField('Data', format='%Y-%m-%dT%H:%M', default=datetime.utcnow, validators=[DataRequired()])
    submit = SubmitField('Adicionar')
