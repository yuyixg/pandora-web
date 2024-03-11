# -*- coding: utf-8 -*-

import logging
from datetime import timedelta
from os.path import join, abspath, dirname
from os import getenv

from flask import Flask, jsonify, make_response, request, Response, render_template, redirect, session, send_from_directory
from flask_cors import CORS
from flask_session import Session
from waitress import serve
from werkzeug.exceptions import default_exceptions
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.serving import WSGIRequestHandler
from datetime import datetime
import re

from .. import __version__
from ..exts.hooks import hook_logging
from ..exts.config import USER_CONFIG_DIR
from ..openai.api import API
from ..openai.utils import Console


class ChatBot:
    __default_ip = '127.0.0.1'
    __default_port = 8009
    
    def __init__(self, chatgpt, debug=False, sentry=False):
        self.chatgpt = chatgpt
        self.debug = debug
        self.sentry = sentry
        self.log_level = logging.DEBUG if debug else logging.WARN
        self.LOCAL_OP = getenv('LOCAL_OP')
        self.SITE_PASSWORD = getenv('PANDORA_SITE_PASSWORD') or getenv('PANDORA_SITE_PASSWD')
        # Console.warn('SITE_PASSWORD: {}'.format(self.SITE_PASSWORD))

        hook_logging(level=self.log_level, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        self.logger = logging.getLogger('waitress')

    def run(self, bind_str, threads=8):
        host, port = self.__parse_bind(bind_str)

        resource_path = abspath(join(dirname(__file__), '..', 'flask'))
        app = Flask(__name__, static_url_path='',
                    static_folder=join(resource_path, 'static'),
                    template_folder=join(resource_path, 'templates'))
        app.wsgi_app = ProxyFix(app.wsgi_app, x_port=1)
        # app.after_request(self.__after_request)

        @app.errorhandler(404)
        def page_not_found(e):
            if request.method == 'GET':
                if request.path.startswith('/c/'):
                    return redirect('/')
                else:
                    return render_template('404.html'), 404
                
            return e

        if self.SITE_PASSWORD == 'I_KNOW_THE_RISKS_AND_STILL_NO_SITE_PASSWORD':
            Console.warn('### You have not set the site password, which is very dangerous!')
            Console.warn('### You have not set the site password, which is very dangerous!')
            Console.warn('### You have not set the site password, which is very dangerous!')

        else:
            app.secret_key = 'PandoraWeb'
            app.config["SESSION_TYPE"] = "filesystem"
            app.config["SESSION_FILE_DIR"] = USER_CONFIG_DIR + '/sessions'

        # dev
        # app.config['TEMPLATES_AUTO_RELOAD'] = True
        
        Session(app)

        CORS(app, resources={r'/api/*': {'supports_credentials': True, 'expose_headers': [
            'Content-Type',
            'Authorization',
            'X-Requested-With',
            'Accept',
            'Origin',
            'Access-Control-Request-Method',
            'Access-Control-Request-Headers',
            'Content-Disposition',
        ], 'max_age': 600}})

        for ex in default_exceptions:
            app.register_error_handler(ex, self.__handle_error)

        app.route('/ces/v1/t')(self.fake_check)    # check
        app.route('/v1/rgstr', methods=['GET', 'POST', 'PATCH'])(self.fake_check)    # check
        app.route('/rgstr', methods=['GET', 'POST', 'PATCH'])(self.fake_check)    # check
        app.route('/backend-api/lat/tti', methods=['GET', 'POST'])(self.fake_check_tti)    # check
        app.route('/backend-api/lat/r', methods=['GET', 'POST'])(self.fake_check_tti)    # check
        app.route('/backend-api/user_surveys/active')(self.fake_check_active)    # check
        app.route('/backend-api/compliance')(self.fake_compliance)    # check
        app.route('/backend-api/models')(self.list_models)
        app.route('/public-api/conversation_limit')(self.fake_conversation_limit)
        app.route('/backend-api/conversations')(self.list_conversations)
        app.route('/backend-api/conversations', methods=['DELETE'])(self.clear_conversations)
        app.route('/backend-api/conversation/<conversation_id>/url_safe', methods=['GET'])(self.fake_url_check)
        app.route('/backend-api/conversation/<conversation_id>')(self.get_conversation)
        app.route('/backend-api/conversation/<conversation_id>', methods=['DELETE', 'PATCH'])(self.del_or_rename_conversation)
        # app.route('/backend-api/conversation/<conversation_id>', methods=['PATCH'])(self.set_conversation_title)
        app.route('/backend-api/conversation/gen_title/<conversation_id>', methods=['POST'])(self.gen_conversation_title)
        app.route('/backend-api/register-websocket', methods=['POST'])(self.register_websocket)
        app.route('/backend-api/conversation', methods=['POST'])(self.talk)
        app.route('/backend-api/conversation/regenerate', methods=['POST'])(self.regenerate)
        app.route('/backend-api/conversation/goon', methods=['POST'])(self.goon)
        # app.route('/backend-api/share/create', methods=['POST'])(self.create_share)  # 饼
        # app.route('/backend-api/share/<share_id>', methods=['PATCH'])(self.fake_create_share_feedback)  # 饼
        # app.route('/share/<share_id>', methods=['GET'])(self.get_share_page)  # 饼

        app.route('/api/auth/session')(self.fake_session)
        app.route('/backend-api/me')(self.fake_me)
        app.route('/backend-api/referral/invites')(self.fake_invites)    # check
        app.route('/backend-api/settings/user')(self.fake_settings_user)
        app.route('/backend-api/prompt_library/')(self.fake_prompt_library)
        app.route('/backend-api/accounts/check/<path:subpath>')(self.acc_check)
        app.route('/_next/data/olf4sv64FWIcQ_zCGl90t/chat.json')(self.fake_chat_info)

        if self.SITE_PASSWORD != 'I_KNOW_THE_RISKS_AND_STILL_NO_SITE_PASSWORD':
            app.route('/login', methods=['GET', 'POST'])(self.login)
            # app.route('/login2', methods=['GET', 'POST'])(self.login2)
            app.route('/auth/logout')(self.logout)
        
        app.route('/')(self.chat)
        app.route('/chat')(self.chat)
        app.route('/chat/<conversation_id>')(self.chat)
        app.route('/img/<path:filename>')(self.get_text_gen_image_file)     # 文生图

        app.route('/backend-api/gizmos/bootstrap')(self.list_models)    # gpts
        # app.route('/backend-api/sentinel/arkose/dx')(self.arkose_dx)    # check
        app.route('/v2/35536E1E-65B4-4D96-9D97-6ADB7EFF8147/settings')(self.fake_arkose_settings)    # check

        # 古早ui
        app.route('/api/models')(self.list_models)
        app.route('/api/conversations')(self.list_conversations)
        app.route('/api/conversations', methods=['DELETE'])(self.clear_conversations)
        app.route('/api/conversation/<conversation_id>')(self.get_conversation)
        app.route('/api/conversation/<conversation_id>', methods=['DELETE'])(self.del_or_rename_conversation)
        app.route('/api/conversation/<conversation_id>', methods=['PATCH'])(self.set_conversation_title)
        # app.route('/api/conversation/gen_title/<conversation_id>', methods=['POST'])(self.gen_conversation_title)
        app.route('/api/conversation/talk', methods=['POST'])(self.talk)
        app.route('/api/conversation/regenerate', methods=['POST'])(self.regenerate)
        app.route('/api/conversation/goon', methods=['POST'])(self.goon)

        app.route('/api/auth/session')(self.fake_session)
        app.route('/api/accounts/check')(self.old_check)
        app.route('/_next/data/olf4sv64FWIcQ_zCGl90t/chat.json')(self.fake_chat_info)

        # app.route('/')(self.chat)
        # app.route('/chat')(self.chat)
        # app.route('/chat/<conversation_id>')(self.chat)

        if not self.debug:
            self.logger.warning('Serving on http://{}:{}'.format(host, port))

        WSGIRequestHandler.protocol_version = 'HTTP/1.1'
        serve(app, host=host, port=port, ident=None, threads=threads)

    @staticmethod
    def __after_request(resp):
        resp.headers['X-Server'] = 'pandora/{}'.format(__version__)

        return resp

    def __parse_bind(self, bind_str):
        sections = bind_str.split(':', 2)
        if len(sections) < 2:
            try:
                port = int(sections[0])
                return self.__default_ip, port
            except ValueError:
                return sections[0], self.__default_port

        return sections[0], int(sections[1])

    def __handle_error(self, e):
        ip = request.remote_addr
        if 'X-Forwarded-For' in request.headers:
                ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
        path = request.path

        if not (path.startswith('/widget') or path.startswith('/backend-api') or path.startswith('/_next') or path.startswith('/v1/initialize') or path.startswith('/auth/js/main.92bf7bcd.js.map')):
            self.logger.error('{}  |  {}  |  {}'.format(ip, path, str(e)))

        if request.path.startswith('/c/') and request.method == 'GET':
                return redirect('/')
        else:
            # return e
            return render_template('404.html'), 404

        # return make_response(jsonify({
        #     'code': e.code,
        #     'message': str(e.original_exception if self.debug and hasattr(e, 'original_exception') else e.name)
        # }), 500)

    @staticmethod
    def __set_cookie(resp, token_key, max_age):
        resp.set_cookie('token-key', token_key, max_age=max_age, path='/', domain=None, httponly=True, samesite='Lax')

    @staticmethod
    def __get_token_key():
        return request.headers.get('X-Use-Token', request.cookies.get('token-key'))
    
    def log(self,date, ip, msg):   
        # 获取IP位置
        # url = "https://whois.pconline.com.cn/ipJson.jsp?ip=" + str(ip)
        # res = requests.get(url).text
        # if res:
        #     result_step1 = res.split('(', 2)[-1]
        #     result = result_step1.rsplit(')', 1)[0]
        #     addr = json.loads(result).get("addr")
        
        # 当请求内容长度大于50时截取
        if len(msg) >50 :
            msg = msg[:50] + "..."

        # 组装log文本
        """
        时间 |   IP |   内容[:50]
        """
        content = date + " |   " + ip + " |   " + msg

        with open(file=USER_CONFIG_DIR + '/login_failed.log', mode='a', encoding="utf-8") as f:
            f.write(content + '\n')
    
    def login(self):
        if request.method == "POST":
            date = datetime.strftime(datetime.now(),'%Y/%m/%d %H:%M:%S')
            ip = request.remote_addr
            if 'X-Forwarded-For' in request.headers:
                ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
            data = request.get_json()
            # self.logger.warning('IP: {} | Password: {}'.format(request.remote_addr, data['password']))
            # self.logger.warning('login data => {}'.format(data))

            if data['password'] == self.SITE_PASSWORD:
                # self.logger.warning('Login success')
                # self.chatgpt.log(date, ip, 'Login success')
                # 登录成功后，保存用户的登录状态到 session
                session["logged_in"] = True
                return redirect("/")
            else:
                # self.logger.warning('{} | {} | {}'.format(date, ip, 'Password Error: '+data['password']))
                self.chatgpt.log(date, ip, 'Password Error: ' + data['password'])
                return make_response(jsonify({"error": "Invalid password"}), 401)
        else:
            if getenv('PANDORA_OLD_LOGIN'):
                return render_template("login_old.html", pandora_base=request.url_root.strip('/login'))
            else:
                return render_template("login_new.html", pandora_base=request.url_root.strip('/login'))
        
    def login2(self):
        return render_template("login_new.html", pandora_base=request.url_root.strip('/login2'))
        
    def logout(self):
        # 退出登录时，移除 session 中的登录状态
        session.pop("logged_in", None)
        return redirect("/login")
    

    def chat(self, conversation_id=None):
        if self.SITE_PASSWORD != 'I_KNOW_THE_RISKS_AND_STILL_NO_SITE_PASSWORD':
            if not session.get("logged_in"):
                return redirect("/login")
    
        query = {'chatId': [conversation_id]} if conversation_id else {}

        token_key = request.args.get('token')

        if getenv('PANDORA_OLD_CHAT'):
            rendered = render_template('PandoraNeverDie.html', pandora_base=request.url_root.strip('/'), query=query)
        else:
            rendered = render_template('chat.html', pandora_base=request.url_root.strip('/'), query=query)

        resp = make_response(rendered)

        if token_key:
            self.__set_cookie(resp, token_key, timedelta(days=30))

        return resp

    @staticmethod
    def fake_session():
        data = {
            'user': {
                'id': 'user-000000000000000000000000',
                'name': 'admin@openai.com',
                'email': 'admin@openai.com',
                'image': None,
                'picture': None,
                'groups': []
            },
            'expires': '2089-08-08T23:59:59.999Z',
            'accessToken': 'secret',
            "authProvider": "auth0",
        }

        return jsonify(data)

    @staticmethod
    def fake_chat_info():
        data = {
            'pageProps': {
                'user': {
                    'id': 'user-000000000000000000000000',
                    'name': 'admin@openai.com',
                    'email': 'admin@openai.com',
                    'image': None,
                    'picture': None,
                    'groups': []
                },
                'serviceStatus': {},
                'userCountry': 'US',
                'geoOk': True,
                'serviceAnnouncement': {
                    'paid': {},
                    'public': {}
                },
                'isUserInCanPayGroup': True
            },
            '__N_SSP': True
        }

        return jsonify(data)

    def acc_check(self, subpath=None):
        data = {
    "accounts": {
        "00000000-0000-0000-0000-000000000001": {
            "account": {
                "account_user_role": "account-owner",
                "account_user_id": "user-000000000000000000000000__00000000-0000-0000-0000-000000000001",
                "processor": {
                    "a001": {
                        "has_customer_object": True
                    },
                    "b001": {
                        "has_transaction_history": False
                    },
                    "c001": {
                        "has_transaction_history": False
                    }
                },
                "account_id": "00000000-0000-0000-0000-000000000001",
                "organization_id": None,
                "is_most_recent_expired_subscription_gratis": False,
                "has_previously_paid_subscription": True,
                "name": None,
                "profile_picture_id": None,
                "profile_picture_url": None,
                "structure": "personal",
                "plan_type": "free",
                "is_deactivated": False,
                "promo_data": {}
            },
            "features": [
                "arkose_noauth",
                "beta_features",
                "bizmo_settings",
                "breeze_available",
                "browsing_available",
                "chat_preferences_available",
                "chatgpt_ios_attest",
                "code_interpreter_available",
                "conversation_bot_arkose",
                "invite_referral",
                "memory_history_enabled",
                "model_switcher",
                "new_plugin_oauth_endpoint",
                "plugins_available",
                "privacy_policy_nov_2023",
                "shareable_links",
                "shared_websocket",
                "starter_prompts",
                "targeted_replies",
                "thumbs_down_only",
                "user_settings_announcements"
            ],
            "entitlement": {
                "subscription_id": "00000000-0000-0000-0000-000000000001",
                "has_active_subscription": True,
                "subscription_plan": "chatgptplusplan",
                "expires_at": "2029-02-24T15:49:46+00:00",
                "billing_period": None
            },
            "last_active_subscription": {
                "subscription_id": "00000000-0000-0000-0000-000000000001",
                "purchase_origin_platform": "chatgpt_web",
                "will_renew": True
            },
            "is_eligible_for_yearly_plus_subscription": False
        },
        "default": {
            "account": {
                "account_user_role": "account-owner",
                "account_user_id": "user-000000000000000000000000__00000000-0000-0000-0000-000000000001",
                "processor": {
                    "a001": {
                        "has_customer_object": True
                    },
                    "b001": {
                        "has_transaction_history": False
                    },
                    "c001": {
                        "has_transaction_history": False
                    }
                },
                "account_id": "00000000-0000-0000-0000-000000000001",
                "organization_id": None,
                "is_most_recent_expired_subscription_gratis": False,
                "has_previously_paid_subscription": True,
                "name": None,
                "profile_picture_id": None,
                "profile_picture_url": None,
                "structure": "personal",
                "plan_type": "free",
                "is_deactivated": False,
                "promo_data": {}
            },
            "features": [
                "arkose_noauth",
                "beta_features",
                "bizmo_settings",
                "breeze_available",
                "browsing_available",
                "chat_preferences_available",
                "chatgpt_ios_attest",
                "code_interpreter_available",
                "conversation_bot_arkose",
                "invite_referral",
                "memory_history_enabled",
                "model_switcher",
                "new_plugin_oauth_endpoint",
                "plugins_available",
                "privacy_policy_nov_2023",
                "shareable_links",
                "shared_websocket",
                "starter_prompts",
                "targeted_replies",
                "thumbs_down_only",
                "user_settings_announcements"
            ],
            "entitlement": {
                "subscription_id": "00000000-0000-0000-0000-000000000001",
                "has_active_subscription": True,
                "subscription_plan": "chatgptplusplan",
                "expires_at": "2029-02-24T15:49:46+00:00",
                "billing_period": None
            },
            "last_active_subscription": {
                "subscription_id": "00000000-0000-0000-0000-000000000001",
                "purchase_origin_platform": "chatgpt_web",
                "will_renew": True
            },
            "is_eligible_for_yearly_plus_subscription": False
        }
    },
    "account_ordering": [
        "00000000-0000-0000-0000-000000000001"
    ]
}

        return jsonify(data)

    def list_models(self):
        referer = request.headers.get('Referer')
        origin = re.match(r'(https?://[^/]+)', referer)
        if origin is not None:
            origin = origin.group(0)
        else:
            origin = ''
        # Console.warn('origin: {}'.format(origin))
        
        return self.__proxy_result(self.chatgpt.list_models(True, self.__get_token_key(), origin))
    
    @staticmethod
    def fake_conversation_limit():
        data = {
                "message_cap": 40.0,
                "message_cap_window": 180.0,
                "message_disclaimer": {
                    "textarea": "GPT-4 currently has a cap of 40 messages every 3 hours.",
                    "model-switcher": "You've reached the GPT-4 cap, which gives all ChatGPT Plus users a chance to try the model.\n\nPlease check back soon."
                }
            }
        return jsonify(data)
    
    @staticmethod
    def fake_url_check(conversation_id=None):
        return jsonify({"safe":True})
    
    @staticmethod
    def fake_check():
        return jsonify({"success":True})
    
    @staticmethod
    def old_check():
        ret = {
            'account_plan': {
                'is_paid_subscription_active': True,
                'subscription_plan': 'chatgptplusplan',
                'account_user_role': 'account-owner',
                'was_paid_customer': True,
                'has_customer_object': True,
                'subscription_expires_at_timestamp': 3774355199
            },
            'user_country': 'US',
            'features': [
                'model_switcher',
                'dfw_message_feedback',
                'dfw_inline_message_regen_comparison',
                'model_preview',
                'system_message',
                'can_continue',
            ],
        }

        return jsonify(ret)
    
    @staticmethod
    def fake_check_tti():
        return jsonify({"status":"success"})
    
    @staticmethod
    def fake_check_active():
        return jsonify({"survey":None})
    
    @staticmethod
    def fake_me():
        user_info = {
                    "object": "user",
                    "id": "user-000000000000000000000000",
                    "email": "admin@openai.com",
                    "name": "PandoraWeb",
                    "picture": None,
                    "created": 1679041742,
                    "phone_number": "+8008208820",
                    "platform_ui_refresh": True,
                    "mfa_flag_enabled": False,
                    "groups": [],
                    "orgs": {
                        "object": "list",
                        "data": [
                            {
                                "object": "organization",
                                "id": "org-E15zUlff1mzdOp3LP9v4cUJe",
                                "created": 1679041742,
                                "title": "Personal",
                                "name": "user-000000000000000000000000",
                                "description": "Personal org for admin@openai.com",
                                "personal": True,
                                "settings": {
                                    "threads_ui_visibility": "NONE",
                                    "usage_dashboard_visibility": "ANY_ROLE"
                                },
                                "is_default": True,
                                "role": "owner",
                                "groups": []
                            }
                        ]
                    },
                    "amr": []
                }
        return jsonify(user_info)
    
    @staticmethod
    def fake_arkose_settings():
        return jsonify({"default":{"settings":{"observability":{"enabled":True,"samplePercentage":1}}}})
    
    @staticmethod
    def fake_settings_user():
        data = {
                "beta_settings": {
                    "plugins": False
                },
                "announcements": {
                    "oai/apps/hasSeenOnboarding": "2024-02-20T13:14:07.104326",
                    "oai/apps/hasSeenPluginsDisclaimer": "2024-02-20T14:28:14.240296",
                    "oai/apps/hasSeenLocaleBanner": "2024-02-20T23:44:51.716606",
                    "oai/apps/hasSeenMentionGPTs": "2024-02-24T12:44:34.761752",
                    "oai/apps/hasSeenArchiveConversationOnboarding": "2024-02-21T10:08:20.001487",
                    "oai/apps/hasUserContextFirstTime/2023-06-29": "2024-02-22T06:32:09.098416"
                },
                "eligible_announcements": [
                    "oai/apps/hasSeenMultiToolAnnouncement",
                    "oai/apps/hasSeenMemoryOnboarding",
                    "oai/apps/hasSeenTemporaryChatOnboarding",
                    "oai/apps/hasSeenTeamOwnerOnboarding"
                ],
                "settings": {
                    "training_allowed": True,
                    "show_expanded_code_view": True
                }
            }

        return jsonify(data)
    
    @staticmethod
    def fake_compliance():
        data = {
                "registration_country": "US",
                "require_cookie_consent": False,
                "terms_of_use": {
                    "is_required": False,
                    "display": None
                },
                "cookie_consent": {
                    "is_required": False,
                    "analytics_cookies_accepted": None
                },
                "age_verification": {
                    "is_required": False,
                    "remaining_seconds": None
                }
            }
        return jsonify(data)
    
    @staticmethod
    def fake_invites():
        data = {"status":"success","claimed_invites":0,"invites_remaining":0,"invite_codes":[]}
        return jsonify(data)
    
    @staticmethod
    def fake_prompt_library():
        data = {
                "items": [
                    {
                        "id": "58d452ea",
                        "title": "Brainstorm edge cases",
                        "description": "for a function with birthdate as input, horoscope as output",
                        "prompt": "Can you brainstorm some edge cases for a function that takes birthdate as input and returns the horoscope?",
                        "category": "idea"
                    },
                    {
                        "id": "c43fd43f",
                        "title": "Write a spreadsheet formula",
                        "description": "to convert a date to the weekday",
                        "prompt": "Can you write me a spreadsheet formula to convert a date in one column to the weekday (like \"Thursday\")?",
                        "category": "code"
                    },
                    {
                        "id": "c45a8f55",
                        "title": "Write a course overview",
                        "description": "on the psychology behind decision-making",
                        "prompt": "Write a 1-paragraph overview for a course called \"The Psychology Of Decision-Making\"",
                        "category": "write"
                    },
                    {
                        "id": "d4675c8e",
                        "title": "Explain options trading",
                        "description": "if I'm familiar with buying and selling stocks",
                        "prompt": "Explain options trading in simple terms if I'm familiar with buying and selling stocks.",
                        "category": "teach-or-explain"
                    }
                ],
                "total": 4,
                "limit": 4,
                "offset": 0
            }
        return jsonify(data)
    
    def register_websocket(self):
        # Console.debug_b('register_websocket => '.format(request.json))

        return self.__proxy_result(self.chatgpt.register_websocket(request, self.__get_token_key()))

    def list_conversations(self):
        offset = request.args.get('offset', '0')
        limit = request.args.get('limit', '28')

        return self.__proxy_result(self.chatgpt.list_conversations(offset, limit, True, self.__get_token_key()))

    def get_conversation(self, conversation_id):

        return self.__proxy_result(self.chatgpt.get_conversation(conversation_id, True, self.__get_token_key()))

    def del_or_rename_conversation(self, conversation_id):
        is_visible = request.json.get('is_visible')
        if is_visible is False:

            return self.__proxy_result(self.chatgpt.del_conversation(conversation_id, True, self.__get_token_key()))
        
        title = request.json.get('title')

        return self.__proxy_result(
            self.chatgpt.set_conversation_title(conversation_id, title, True, self.__get_token_key()))

    def clear_conversations(self):

        return self.__proxy_result(self.chatgpt.clear_conversations(True, self.__get_token_key()))

    def set_conversation_title(self, conversation_id):
        title = request.json['title']

        return self.__proxy_result(
            self.chatgpt.set_conversation_title(conversation_id, title, True, self.__get_token_key()))

    def gen_conversation_title(self, conversation_id):
        payload = request.json
        # model = payload['model']      # 新ui无model参数
        message_id = payload['message_id']

        return self.__proxy_result(
            self.chatgpt.gen_conversation_title(conversation_id, message_id, True, self.__get_token_key()))

    def talk(self):
        payload = request.json
        try:
            prompt = payload['messages'][0]['content']['parts'][0]
            model = payload['model']
            message_id = payload['messages'][0]['id']
        except KeyError:
            # 兼容旧ui参数
            prompt = payload['prompt']
            model = payload['model']
            message_id = payload['message_id']

        parent_message_id = payload['parent_message_id']
        conversation_id = payload.get('conversation_id')
        stream = payload.get('stream', True)

        if model == 'text-davinci-002-render-sha':
            gpt35_model = getenv('PANDORA_GPT35_MODEL')
            if not gpt35_model:

                return self.__proxy_result(self.chatgpt.chat_ws(payload, self.__get_token_key()))
            
            else:
                model = gpt35_model
        
        # if model == 'stable-diffusion-xl-base-1.0' or model == 'dreamshaper-8-lcm' or model == 'stable-diffusion-xl-lightning':
        #     return self.__proxy_result(self.chatgpt.cfai_text2img(payload, self.__get_token_key()))

        return self.__process_stream(
            *self.chatgpt.talk(prompt, model, message_id, parent_message_id, conversation_id, stream,
                               self.__get_token_key()), stream)

    def goon(self):
        payload = request.json
        model = payload['model']
        parent_message_id = payload['parent_message_id']
        conversation_id = payload.get('conversation_id')
        stream = payload.get('stream', True)

        return self.__process_stream(
            *self.chatgpt.goon(model, parent_message_id, conversation_id, stream, self.__get_token_key()), stream)

    def regenerate(self):
        payload = request.json

        conversation_id = payload.get('conversation_id')
        if not conversation_id:
            return self.talk()

        prompt = payload['prompt']
        model = payload['model']
        message_id = payload['message_id']
        parent_message_id = payload['parent_message_id']
        stream = payload.get('stream', True)

        return self.__process_stream(
            *self.chatgpt.regenerate_reply(prompt, model, conversation_id, message_id, parent_message_id, stream,
                                           self.__get_token_key()), stream)
    
    def arkose_dx(self):
        return self.__proxy_result(self.chatgpt.arkose_dx(request, self.__get_token_key()))
    

    def create_share(self):
        return self.__proxy_result(
            self.chatgpt.create_share(request, self.__get_token_key()))
    
    def fake_create_share_feedback(self, share_id):
        feedback_data = {
                        "moderation_state": {
                            "has_been_moderated": False,
                            "has_been_blocked": False,
                            "has_been_accepted": False,
                            "has_been_auto_blocked": False,
                            "has_been_auto_moderated": False
                        }
                    }
        return jsonify(feedback_data)
    
    def get_share_page(self, share_id):
        page_data = self.chatgpt.get_share_data(share_id, self.__get_token_key())

        return render_template('share.html', data = page_data)
    
    def get_text_gen_image_file(self, filename):
        return send_from_directory(USER_CONFIG_DIR+'/text2img', filename)

    @staticmethod
    def __process_stream(status, headers, generator, stream):
        if stream:
            return Response(API.wrap_stream_out(generator, status), mimetype=headers['Content-Type'], status=status)

        last_json = None
        for json in generator:
            last_json = json

        return make_response(last_json, status)

    @staticmethod
    def __proxy_result(remote_resp):
        if remote_resp == 404:  # 对于本需要透传的url, 当不启用OAI服务时直接return 404
            # 不启用OAI服务时避免一堆报错
            remote_resp = Response()
            remote_resp.status = 404
            remote_resp.text = b''
            remote_resp.content_type = 'text/html; charset=utf-8'

        resp = make_response(remote_resp.text)
        resp.content_type = remote_resp.headers['Content-Type']
        resp.status_code = remote_resp.status_code

        return resp
