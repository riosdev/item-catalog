from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, GrupoAlimentar, Alimento
from flask import session as login_session
from flask import make_response
import random
import json
import httplib2
import string
import requests
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

# Habilitar comunicacao com o banco de dados
engine = create_engine(
    'sqlite:///gruposalimentares.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# carregar client_secrets para permitir login
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalogo de Grupos Alimentares"


@app.route('/grupo_alimentar/<int:food_group_id>/alimento/JSON')
def grupoAlimentarJSON(food_group_id):
    items = session.query(Alimento).filter_by(
        food_group_id=food_group_id).all()
    return jsonify(Alimento=[i.serialize for i in items])


@app.route('/grupo_alimentar/<int:food_group_id>/alimento/<int:food_id>/JSON')
def alimentoJSON(food_group_id, food_id):
    alimento = session.query(Alimento).filter_by(id=food_id).one()
    return jsonify(Alimento=alimento.serialize)


@app.route('/grupo_alimentar/JSON')
def gruposAlimentaresJSON():
    grupos_alimentares = session.query(GrupoAlimentar).all()
    return jsonify(
        grupos_alimentares=[r.serialize for r in grupos_alimentares])


# CRUD - GrupoAlimentar
# CREATE
@app.route('/grupo_alimentar/novo/', methods=['GET', 'POST'])
def criarGrupoAlimentar():
    # Solicitar login para criar grupo alimentar
    if 'email' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        item = GrupoAlimentar(name=request.form['name'])
        # Registrar usuario que criou o grupo alimentar
        item.addedby = login_session['email']
        session.add(item)
        session.commit()
        return redirect(url_for('exibirGruposAlimentares'))
    else:
        return render_template('criarGrupoAlimentar.html')


# READ
@app.route('/')
@app.route('/grupo_alimentar/')
def exibirGruposAlimentares():
    grupos_alimentares = session.query(GrupoAlimentar).all()
    return render_template('gruposAlimentares.html',
                           grupos_alimentares=grupos_alimentares)


# UPDATE
@app.route('/grupo_alimentar/<int:food_group_id>/edit/',
           methods=['GET', 'POST'])
def modificarGrupoAlimentar(food_group_id):
    # Solicitar login para modificar grupo alimentar
    if 'email' not in login_session:
        return redirect('/login')
    item = session.query(GrupoAlimentar).filter_by(id=food_group_id).one()
    # Verificar se o usuario possui permissao para modificar
    if item.addedby != login_session['email']:
        return redirect('/denied')
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
            return redirect(url_for('exibirGruposAlimentares'))
    else:
        return render_template(
            'modificarGrupoAlimentar.html', grupo_alimentar=item)


# DELETE
@app.route('/grupo_alimentar/<int:food_group_id>/apagar/',
           methods=['GET', 'POST'])
def apagarGrupoAlimentar(food_group_id):
    # Solicitar login para apagar grupo alimentar
    if 'email' not in login_session:
        return redirect('/login')
    item = session.query(GrupoAlimentar).filter_by(id=food_group_id).one()
    # Verificar se o usuario possui permissao para apagar
    if item.addedby != login_session['email']:
        return redirect('/denied')
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(
            url_for('exibirGruposAlimentares', food_group_id=food_group_id))
    else:
        return render_template(
            'apagarGrupoAlimentar.html', grupo_alimentar=item)


# CRUD - Alimento
# CREATE
@app.route('/grupo_alimentar/<int:food_group_id>/alimento/novo/',
           methods=['GET', 'POST'])
def criarAlimento(food_group_id):
    # Solicitar login para criar alimento
    if 'email' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        item = Alimento(name=request.form['name'],
                        description=request.form['description'],
                        calories=request.form['calories'],
                        weight=request.form['weight'],
                        food_group_id=food_group_id)
        # Registrar usuario que criou o alimento
        item.addedby = login_session['email']
        session.add(item)
        session.commit()
        return redirect(url_for('exibirAlimentos',
                                food_group_id=food_group_id))
    else:
        return render_template('criarAlimento.html',
                               food_group_id=food_group_id)

    return render_template('criarAlimento.html', grupo_alimentar=item)


# READ
@app.route('/grupo_alimentar/<int:food_group_id>/')
@app.route('/grupo_alimentar/<int:food_group_id>/alimento/')
def exibirAlimentos(food_group_id):
    grupo_alimentar = session.query(GrupoAlimentar).filter_by(
        id=food_group_id).one()
    items = session.query(Alimento).filter_by(
        food_group_id=food_group_id).all()
    return render_template('alimentos.html',
                           items=items,
                           grupo_alimentar=grupo_alimentar)


# UPDATE
@app.route('/grupo_alimentar/<int:food_group_id>/alimento/<int:food_id>/modificar',  # noqa
           methods=['GET', 'POST'])
def modificarAlimento(food_group_id, food_id):
    # Solicitar login para modificar o alimento
    if 'email' not in login_session:
        return redirect('/login')
    item = session.query(Alimento).filter_by(id=food_id).one()
    # Verificar se o usuario possui permissao para modificar
    if item.addedby != login_session['email']:
        return redirect('/denied')
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['calories']:
            item.price = request.form['calories']
        if request.form['weight']:
            item.course = request.form['weight']
        session.add(item)
        session.commit()
        return redirect(url_for('exibirAlimentos',
                                food_group_id=food_group_id))
    else:
        return render_template(
            'modificarAlimento.html', food_group_id=food_group_id,
            food_id=food_id, item=item)


# DELETE
@app.route('/grupo_alimentar/<int:food_group_id>/alimento/<int:food_id>/apagar',  # noqa
    methods=['GET', 'POST'])
def apagarAlimento(food_group_id, food_id):
    # Solicitar login para apagar o alimento
    if 'email' not in login_session:
        return redirect('/login')
    item = session.query(Alimento).filter_by(id=food_id).one()
    # Verificar se o usuario possui permissao para apagar
    if item.addedby != login_session['email']:
        return redirect('/denied')
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('exibirAlimentos',
                                food_group_id=food_group_id))
    else:
        return render_template('apagarAlimento.html', item=item)


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Atualizar o codigo de autorizacao para um objeto credentials
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verificar se o token de acesso eh valido
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # Se ocorrer um erro, abortar
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verificar se o token de acesso eh para o usuario correto
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verificar se o token de acesso eh valido para essa aplicacao
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Salvar o token de acesso para usos posteriores
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    # Pegar informacoes do usuario
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['email'] = data['email']

    output = ''
    output += '<h3>Welcome, '
    output += login_session['email']
    output += '!</h3>'
    print "done!"
    return output


# Codigo para habilitar login/logout vem abaixo
@app.route('/gdisconnect')
def gdisconnect():
    # Desconectar somente se houver usuario conectado
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'Email is: '
    print login_session['email']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        # Se por algum motivo, o token foir invalido
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Pagina de permissao negada
@app.route('/denied')
def denied():
    return render_template('denied.html')

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
