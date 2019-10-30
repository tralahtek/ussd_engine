from celery import current_app as app
import requests
from structlog import get_logger
from celery.exceptions import MaxRetriesExceededError
from ussd.session_store import SessionStore
from simplekv import KeyValueStore
from simplekv.fs import FilesystemStore


@app.task(bind=True)
def http_task(self, request_conf):
    requests.request(**request_conf)


@app.task(bind=True)
def report_session(self, session_id, screen_content, session_store_backend: KeyValueStore = FilesystemStore("./session_data"),):
    # to avoid circular import
    from ussd.core import UssdHandlerAbstract

    logger = get_logger(__name__).bind(
        action="report_session_task", session_id=session_id
    )

    logger.info('start')

    ussd_report_session_data = screen_content['ussd_report_session']

    session = SessionStore(session_key=session_id,
                           kv_store=session_store_backend)

    if session.get('posted'):
        logger.info("session_already_reported", posted=session['posted'])
        return

    request_conf = UssdHandlerAbstract.render_request_conf(
        session,
        ussd_report_session_data['request_conf']
    )

    UssdHandlerAbstract.make_request(
        http_request_conf=request_conf,
        response_session_key_save=ussd_report_session_data['session_key'],
        session=session,
        logger=logger
    )

    # check if it is the desired effect
    for expr in ussd_report_session_data['validate_response']:
        if UssdHandlerAbstract.evaluate_jija_expression(
                expr['expression'],
                session=session
        ):
            session['posted'] = True
            session.save()
            return

    if ussd_report_session_data.get('retry_mechanism'):
        try:
            self.retry(**screen_content[
                'ussd_report_session']['retry_mechanism'])
        except MaxRetriesExceededError as e:
            logger.warning("report_session_error", error_message=str(e))
