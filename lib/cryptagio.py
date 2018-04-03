import requests
from electroncash.i18n import _
from decimal import Decimal


class Cryptagio(object):

    def __init__(self, parent):
        self.parent = parent
        self.is_loading = False

    def set_params(self):
        self.currency_code = "BCH"
        self.cryptagio_host = self.parent.config.get('cryptagio_host', '')
        self.cryptagio_host = self.cryptagio_host.rstrip('/')
        self.cryptagio_key = self.parent.config.get('cryptagio_key', '')
        self.headers = {
            'x-api-key': self.cryptagio_key
        }

        self.tx_id = None
        self.max_fee_amount = None  # TODO: use this some way
        self.tx_body_hash = None
        self.max_fee_amount = None

    def check_for_uncorfimed_tx(self):
        if self.is_loading:
            return self.parent.show_error(_('Data load is in process. Please wait'))

        self.is_loading = True

        def make_request():
            self.set_params()
            if self.cryptagio_host == '' or self.cryptagio_key == '':
                return self.parent.show_error(_('Check your Cryptagio preferences'))
            api_requests_route = self.cryptagio_host + "/wallet/" + self.currency_code + "/transaction"

            r = requests.get(api_requests_route, headers=self.headers, params={})

            if r.status_code is not requests.codes.ok:
                return self.parent.show_error(
                    _('Bad response from Cryptagio. Code: ') + ("%s" % r.status_code) + r.text)

            response = r.json()
            if not len(response):
                return None, None, None
            self.tx_id = response['Id']
            self.tx_body_hash = response['TxbodyHash']
            self.max_fee_amount = Decimal(response['MaxFee'])*1000 #in uBTC
            return response['TxHash'], response['Fee'], response['Txbody']

        tx_hash, fee, tx_body = None, None, None
        try:
            tx_hash, fee, tx_body = make_request()
        except Exception as err:
            print(err)
            self.parent.show_error(_('Exception during check_for_uncorfimed_tx request'))

        self.is_loading = False

        return tx_hash, fee, tx_body

    def get_outputs(self):
        if self.is_loading:
            return self.parent.show_error(_('Data load is in process. Please wait'))

        self.is_loading = True

        def make_request():
            outputs = []
            self.set_params()
            if self.cryptagio_host == '' or self.cryptagio_key == '':
                return self.parent.show_error(_('Check your Cryptagio preferences'))

            api_requests_route = self.cryptagio_host + "/wallet/" + self.currency_code + "/request"

            r = requests.get(api_requests_route, headers=self.headers, params={})

            if r.status_code is not requests.codes.ok:
                return self.parent.show_error(
                    _('Bad response from Cryptagio. Code: ') + ("%s" % r.status_code) + r.text)

            response = r.json()

            if not len(response.get('requests', [])):
                return self.parent.show_message(_('No new withdrawal requests yet'))

            self.tx_id = response.get('tx_id', 0)
            if not self.tx_id:
                return self.parent.show_error(_('No tx_id in Cryptagio response'))

            self.max_fee_amount = Decimal(response.get('max_fee_amount', 0))*1000 #in uBTC
            if not self.max_fee_amount:
                return self.parent.show_error(_('No max_fee_amount in Cryptagio response'))

            for item in response.get('requests', []):
                address = item.get('address', '')
                amount = int(item.get('amount', ''))
                if address == '' or amount == '':
                    return self.parent.show_error(_('Bad response from Cryptagio. Address or amount is empty'))

                obj_type, address = self.parent.payto_e.parse_output(address)
                outputs.append((obj_type, address, amount))

            return outputs

        outputs = []
        try:
            outputs = make_request()
        except Exception as err:
            print(err)
            self.parent.show_error(_('Exception during get_outputs request'))

        self.is_loading = False
        return outputs

    def update_tx(self, tx_id, tx_hash, fee, tx_body, tx_prev_body_hash):
        if self.is_loading:
            return self.parent.show_error(_('Data load is in process. Please wait'))

        self.is_loading = True

        def make_request():
            api_tx_route = self.cryptagio_host + "/wallet/" + self.currency_code + "/transaction/" + str(tx_id)
            r = requests.post(api_tx_route, headers=self.headers, data={
                'tx_hash': tx_hash,
                'tx_body': tx_body,
                'fee': fee,
                'tx_prev_body_hash': tx_prev_body_hash,
                # 'state': "Processing", # this one sets automatically
            })
            if r.status_code is not requests.codes.ok:
                return self.parent.show_error(
                    _('Bad response from Jackhammer. Code: ') + ("%s" % r.status_code) + r.text)
            response = r.json()

            return response['tx_body_hash']

        tx_body_hash = ""
        try:
            tx_body_hash = make_request()
        except Exception as err:
            self.parent.show_error(_('Exception during update_tx request'))

        self.is_loading = False

        return tx_body_hash

    def approve_tx(self, tx_id, tx_body, tx_prev_body_hash):
        if self.is_loading:
            return self.parent.show_error(_('Data load is in process. Please wait'))

        self.is_loading = True

        def make_request():
            api_tx_route = self.cryptagio_host + "/wallet/" + self.currency_code + "/transaction/" + str(tx_id)
            r = requests.post(api_tx_route, headers=self.headers, data={
                'tx_body': tx_body,
                'tx_prev_body_hash': tx_prev_body_hash,
                'state': "Done",
            })
            if r.status_code is not requests.codes.ok:
                return self.parent.show_error(
                    _('Bad response from Jackhammer. Code: ') + ("%s" % r.status_code) + r.text)
            response = r.json()

            return response['tx_body_hash']

        tx_body_hash = ""
        try:
            tx_body_hash = make_request()
        except Exception as err:
            self.parent.show_error(_('Exception during update_tx request'))

        self.is_loading = False

        return tx_body_hash
