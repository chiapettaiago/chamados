from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, make_response, Response
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from io import StringIO, BytesIO
import csv
from flask import Response
from datetime import datetime

from .extensions import db
from .models import User, Ticket, Interaction
from .forms import LoginForm, TicketForm, InteractionForm, RegisterForm
from .notify import send_email, send_whatsapp

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    query = Ticket.query
    if current_user.role != 'admin':
        query = query.filter_by(created_by=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Ticket.title.ilike(like), Ticket.description.ilike(like), Ticket.vendor.ilike(like)))
    if status:
        query = query.filter_by(status=status)
    tickets = query.order_by(Ticket.updated_at.desc()).all()
    # Enviar uma notificação simples para chamados estagnados (+24h) do usuário
    if current_user.role != 'admin':
        stale = [t for t in tickets if t.is_stale_24h]
        if stale:
            subj = "Chamados sem interação há 24h"
            body = "<p>Você possui chamados sem interação há mais de 24h:</p><ul>" + "".join([f"<li>#{t.id} - {t.title}</li>" for t in stale]) + "</ul>"
            send_email(current_user.email, subj, body)
    t_form = TicketForm()
    t_form.assignee.data = current_user.name  # auto-preencher responsável
    return render_template('index.html', tickets=tickets, q=q, status=status, t_form=t_form, now=datetime.utcnow())


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Usuário inativo', 'warning')
            else:
                login_user(user, remember=form.remember.data)
                return redirect(url_for('main.index'))
        else:
            flash('Credenciais inválidas', 'danger')
    return render_template('login.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@main_bp.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def ticket_new():
    form = TicketForm()
    if request.method == 'GET':
        form.assignee.data = current_user.name  # auto-preencher responsável
    if form.validate_on_submit():
        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            vendor=form.vendor.data,
            assignee=current_user.name,  # força responsável = usuário logado
            created_by=current_user.id,
        )
        db.session.add(ticket)
        db.session.commit()
        # Notificar o criador
        subj = f"Novo chamado #{ticket.id}: {ticket.title}"
        html = f"<p>Seu chamado foi criado.</p><p>Status: {ticket.status}</p>"
        send_email(current_user.email, subj, html)
        if current_user.phone_e164:
            send_whatsapp(current_user.phone_e164.lstrip('+'), f"Novo chamado #{ticket.id}: {ticket.title}")
        flash('Chamado criado', 'success')
        return redirect(url_for('main.index'))
    return render_template('ticket_form.html', form=form, action='Novo')


@main_bp.route('/tickets/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def ticket_edit(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != 'admin' and ticket.created_by != current_user.id:
        flash('Sem permissão para editar este chamado', 'warning')
        return redirect(url_for('main.index'))
    old_status = ticket.status
    form = TicketForm(obj=ticket)
    if form.validate_on_submit():
        # manter responsável como está ou permitir admin alterar
        if current_user.role == 'admin':
            form.populate_obj(ticket)
        else:
            # Usuário comum não altera o responsável
            ticket.title = form.title.data
            ticket.description = form.description.data
            ticket.status = form.status.data
            ticket.priority = form.priority.data
            ticket.vendor = form.vendor.data
        db.session.commit()
        if ticket.status != old_status:
            subj = f"Chamado #{ticket.id} atualizado para {ticket.status}"
            html = f"<p>Seu chamado mudou de status:</p><p>De: {old_status} → Para: {ticket.status}</p>"
            send_email(ticket.creator.email, subj, html)
            if ticket.creator.phone_e164:
                send_whatsapp(ticket.creator.phone_e164.lstrip('+'), f"Chamado #{ticket.id}: {old_status} → {ticket.status}")
        flash('Chamado atualizado', 'success')
        return redirect(url_for('main.ticket_detail', ticket_id=ticket.id))
    return render_template('ticket_form.html', form=form, action='Editar')


@main_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != 'admin' and ticket.created_by != current_user.id:
        flash('Sem permissão para visualizar este chamado', 'warning')
        return redirect(url_for('main.index'))
    i_form = InteractionForm()
    return render_template('ticket_detail.html', ticket=ticket, i_form=i_form, now=datetime.utcnow())


@main_bp.route('/tickets/<int:ticket_id>/delete', methods=['POST'])
@login_required
def ticket_delete(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != 'admin' and ticket.created_by != current_user.id:
        flash('Sem permissão para excluir', 'warning')
        return redirect(url_for('main.index'))
    db.session.delete(ticket)
    db.session.commit()
    flash('Chamado excluído', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/tickets/<int:ticket_id>/interactions', methods=['POST'])
@login_required
def interaction_add(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != 'admin' and ticket.created_by != current_user.id:
        flash('Sem permissão para interagir neste chamado', 'warning')
        return redirect(url_for('main.index'))
    i_form = InteractionForm()
    if i_form.validate_on_submit():
        inter = Interaction(
            ticket_id=ticket.id,
            content=i_form.content.data,
            author=i_form.author.data,
            created_at=i_form.created_at.data
        )
        db.session.add(inter)
        db.session.commit()
        flash('Interação adicionada', 'success')
    else:
        flash('Erro ao adicionar interação', 'danger')
    return redirect(url_for('main.ticket_detail', ticket_id=ticket.id))


@main_bp.route('/export/csv')
@login_required
def export_csv():
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    query = Ticket.query
    if current_user.role != 'admin':
        query = query.filter_by(created_by=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Ticket.title.ilike(like), Ticket.description.ilike(like), Ticket.vendor.ilike(like)))
    if status:
        query = query.filter_by(status=status)
    tickets = query.order_by(Ticket.updated_at.desc()).all()

    status_labels = {
        'aberto': 'Aberto',
        'pendente_totvs': 'Pendente TOTVS',
        'pendente_feso': 'Pendente FESO',
        'validacao_cliente': 'Validação Cliente',
        'fechado': 'Fechado',
    }

    def fmt_dt(dt):
        return dt.strftime('%d/%m/%Y %H:%M') if dt else ''

    def fmt_td(td):
        try:
            total = int(td.total_seconds())
        except Exception:
            return ''
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    si = StringIO()
    # Dica para Excel usar ';' como separador
    si.write('sep=;\n')
    cw = csv.writer(si, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    cw.writerow(['ID', 'Título', 'Status', 'Prioridade', 'Terceirizada', 'Responsável', 'Criado por', 'Aberto há (HH:MM:SS)', 'Criado em', 'Atualizado em', 'Última interação', 'Alerta 24h'])

    now = datetime.utcnow()
    for t in tickets:
        aberto_ha = fmt_td(now - (t.created_at or now))
        last_inter = getattr(t, 'last_contact_at', None)
        cw.writerow([
            t.id,
            t.title,
            status_labels.get(t.status, t.status),
            t.priority,
            t.vendor or '',
            t.assignee or '',
            t.creator.email,
            aberto_ha,
            fmt_dt(t.created_at),
            fmt_dt(t.updated_at),
            fmt_dt(last_inter),
            'Sim' if getattr(t, 'is_stale_24h', False) else 'Não'
        ])

    output = si.getvalue()
    # Adicionar BOM para Excel reconhecer UTF-8
    output = '\ufeff' + output

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M')
    filename = f'chamados_{ts}.csv'

    return Response(
        output,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@main_bp.route('/export/xlsx')
@login_required
def export_xlsx():
    try:
        import pandas as pd  # lazy import
    except ImportError:
        flash('Exportação XLSX indisponível: instale/repare pandas e numpy (pip install --upgrade pip setuptools wheel; pip install --force-reinstall numpy pandas openpyxl).', 'danger')
        return redirect(url_for('main.index'))

    q = request.args.get('q', '')
    status = request.args.get('status', '')
    query = Ticket.query
    if current_user.role != 'admin':
        query = query.filter_by(created_by=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Ticket.title.ilike(like), Ticket.description.ilike(like), Ticket.vendor.ilike(like)))
    if status:
        query = query.filter_by(status=status)
    tickets = query.order_by(Ticket.updated_at.desc()).all()

    status_labels = {
        'aberto': 'Aberto',
        'pendente_totvs': 'Pendente TOTVS',
        'pendente_feso': 'Pendente FESO',
        'validacao_cliente': 'Validação Cliente',
        'fechado': 'Fechado',
    }

    def fmt_dt(dt):
        return dt.strftime('%d/%m/%Y %H:%M') if dt else ''

    def fmt_td(td):
        try:
            total = int(td.total_seconds())
        except Exception:
            return ''
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    now = datetime.utcnow()
    data = []
    for t in tickets:
        data.append({
            'ID': t.id,
            'Título': t.title,
            'Status': status_labels.get(t.status, t.status),
            'Prioridade': t.priority,
            'Terceirizada': t.vendor or '',
            'Responsável': t.assignee or '',
            'Criado por': t.creator.email,
            'Aberto há (HH:MM:SS)': fmt_td(now - (t.created_at or now)),
            'Criado em': fmt_dt(t.created_at),
            'Atualizado em': fmt_dt(t.updated_at),
            'Última interação': fmt_dt(getattr(t, 'last_contact_at', None)),
            'Alerta 24h': 'Sim' if getattr(t, 'is_stale_24h', False) else 'Não'
        })

    df = pd.DataFrame(data)
    metrics = df.groupby('Status', as_index=False).size().rename(columns={'size': 'Quantidade'}) if not df.empty else pd.DataFrame(columns=['Status','Quantidade'])

    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Chamados')
        metrics.to_excel(writer, index=False, sheet_name='Métricas')
        # Ajuste simples de largura
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_length = 12
                column = col[0].column_letter
                for cell in col:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[column].width = min(max_length + 2, 50)

    bio.seek(0)
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M')
    filename = f'chamados_{ts}.xlsx'
    return send_file(bio, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Email já cadastrado', 'warning')
        else:
            u = User(name=form.name.data, email=form.email.data.lower(), role='user', phone_e164=form.phone_e164.data or None)
            u.set_password(form.password.data)
            db.session.add(u)
            db.session.commit()
            flash('Conta criada. Faça login.', 'success')
            return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@main_bp.route('/theme/toggle')
@login_required
def theme_toggle():
    theme = request.cookies.get('theme', 'light')
    new_theme = 'dark' if theme != 'dark' else 'light'
    resp = make_response(redirect(request.referrer or url_for('main.index')))
    resp.set_cookie('theme', new_theme, max_age=60*60*24*365)
    return resp


@main_bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    from .forms import RequestResetForm
    form = RequestResetForm()
    if form.validate_on_submit():
        # Aqui você geraria um token e enviaria por email
        flash('Se o email existir, um link de redefinição foi enviado.', 'info')
        return redirect(url_for('main.login'))
    return render_template('forgot.html', form=form)


@main_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    from .forms import ResetPasswordForm
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Validar token e atualizar senha do usuário
        flash('Senha redefinida. Faça login.', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset.html', form=form)
