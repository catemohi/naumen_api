import logging
from typing import Any, Mapping, Sequence, Tuple, Type, Union

from requests import exceptions

from .config.structures import ActiveConnect, SearchType, StatusType, TypeReport
from .exceptions import CantGetData, ConnectionsFailed, InvalidDate
from .transceiver.crm import DOMAIN, get_session
from .transceiver.reports import get_report
from .transceiver.response_creator import (
    FORMATTED_RESPONSE,
    JSONResponseFormatter,
    ResponseFormatter,
    ResponseTemplate,
    make_response,
)
from .transceiver.search import search

log = logging.getLogger(__name__)


class Client:

    """Класс для взаимодействия с системой Naumen.
    Возвращает ответы JSON строками.
    """

    def __init__(
        self,
        *,
        username: str = "",
        password: str = "",
        domain: DOMAIN = "",
        formatter: Type[ResponseFormatter] = JSONResponseFormatter,
    ) -> None:

        """Инициализация клиента api. Принимает именнованные аргументы.

        Kwargs:
            username (str): Логин в системе. По умолчанию ''.
            password (str): Пароль в системе. По умолчанию ''.
            domain (DOMAIN): Домен. По умолчанию ''.
        """
        log.debug("Инициализация клиента API.")
        log.debug(
            f"Переданы параметры: username: {username};"
            f"password: {password};domain: {domain}.",
        )
        self.username = username
        self.password = password
        self.domain = domain
        self.formatter = formatter
        self._session: Union[ActiveConnect, None] = None

    def connect(
        self,
        *,
        username: str = "",
        password: str = "",
        domain: DOMAIN = "",
    ) -> FORMATTED_RESPONSE:

        """Метод для соединение с системой NAUMEN.
           Принимает именнованные аргументы.

        Kwargs:
            username (str, optional): Логин в системе. По умолчанию ''.
            password (str, optional): Пароль в системе. По умолчанию ''.
            domain (DOMAIN, optional): Домен. По умолчанию ''.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        """

        log.debug("Создание соединения с CRM NAUMEN.")
        log.debug(
            f"Переданы параметры: username: {username};"
            f"password: {password};domain: {domain}.",
        )
        local_credentials = all([username, password, domain])
        self_credentials = all([self.username, self.password, self.domain])
        error_response = ResponseTemplate(StatusType._UNAUTHORIZED, ())

        if not any([local_credentials, self_credentials]):
            log.error("Не передано данных для соединения с CRM NAUMEN.")
            return make_response(error_response, self.formatter)

        if local_credentials:
            self.username = username
            self.password = password
            self.domain = domain
        try:
            self._session = get_session(self.username, self.password, self.domain)
            log.info("Соединение с CRM NAUMEN успешно установлено.")
            success_response = ResponseTemplate(StatusType._SUCCESS, ())
            return make_response(success_response, self.formatter)

        except ConnectionsFailed:
            logging.exception("Ошибка соединения с CRM NAUMEN.")
            return make_response(error_response, self.formatter)

    def search_issue(
        self,
        *args: Sequence,
        number: Union[str, int] = "",
        name_contragent: str = "",
        number_contragent: Union[str, int] = "",
        parse_issue_history: bool = False,
        parse_issue_card: bool = False,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:
        """Метод для получения для поиска обращения

        Args:
            number (int): номер обращения.
            name_contragent (str): имя контрагента.
            number_contragent (int): номер контрагента.
            parse_issue_card (bool): собирать ли информацию с карточки обращения
            parse_issue_history (bool): собирать ли информацию о работе по задаче
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:


        """
        log.debug("Поиск обращений по критериям.")
        log.debug(
            f"Параметр byNumber: {number}; "
            f"Параметр byCntrTitle: {name_contragent}; "
            f"Параметр byCntrNumber: {number_contragent};",
        )

        _ = {
            "byNumber": number,
            "byCntrTitle": name_contragent,
            "byCntrNumber": number_contragent,
        }
        add_kwarg: Mapping = {
            "parse_issue_history": parse_issue_history,
            "parse_issue_cards": parse_issue_card,
        }
        report_kwargs = tuple(_.items())
        return self._get_response(
            SearchType.ISSUES_SEARCH,
            mod_data=report_kwargs,
            mod_params=(),
            **add_kwarg,
        )

    def get_issues(
        self,
        *args: Sequence,
        is_vip: bool = False,
        parse_issue_history: bool = False,
        parse_issue_card: bool = False,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:

        """Метод для получения отчёта о проблемах на линии ТП.

        Args:
            is_vip: флаг указывающий на то, тикеты какой линии получить.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        report = TypeReport.ISSUES_VIP_LINE if is_vip else TypeReport.ISSUES_FIRST_LINE

        log.debug("Запрос открытых проблем техподдержки.")
        log.debug(f"Параметр is_vip: {is_vip}")

        report_kwargs: Mapping = {
            "parse_issue_history": parse_issue_history,
            "parse_issue_cards": parse_issue_card,
        }
        return self._get_response(report, mod_params=(), mod_data=(), **report_kwargs)

    def get_issue_card(
        self,
        naumen_uuid: str,
        *args: Sequence,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:

        """Метод для получения данных с карточки обращения

        Args:
            naumen_uuid: uuid обращения в CRM NAUMEN.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        report = TypeReport.ISSUE_CARD
        log.debug("Запрос данных с карточки обращения.")
        report_kwargs: Mapping = {"naumen_uuid": naumen_uuid}
        return self._get_response(report, mod_params=(), mod_data=(), **report_kwargs)

    def get_sl_report(
        self,
        start_date: str,
        end_date: str,
        deadline: int = 15,
        *args: Sequence,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:

        """Метод для получения отчёта о Service Level за период.
           Метод возвращает дни, без привязки к месяцу.
           Если передать период с 01.05.2022 по 01.07.2022
           вернется отчет за 31 день, процент дня будет средним
           за два месяца.

        Args:
            start_date: дата начала периода.
            end_date: дата конца периода.
            deadline: количество минут относительно которых
            считать service level.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        log.debug("Запрос service level техподдержки.")
        try:
            deadline = int(deadline)
        except (ValueError, TypeError):
            logging.exception(
                f"Аргумент deadline не int и" f"не валидный литерал: " f"{deadline}",
            )
            error_response = ResponseTemplate(StatusType._BAD_REQUEST, ())
            error_response.status.description = (
                f"Invalid deadline value: " f"{deadline}"
            )
            return make_response(error_response, self.formatter)

        log.debug(
            f"Параметр start_date: {start_date}; "
            f"Параметр end_date: {end_date}; "
            f"Параметр deadline: {deadline}; ",
        )

        _ = {
            "start_date": start_date,
            "end_date": end_date,
            "deadline": deadline,
        }
        report_kwargs = tuple(_.items())
        return self._get_response(
            TypeReport.SERVICE_LEVEL,
            mod_data=report_kwargs,
            mod_params=(),
            **kwargs,
        )

    def get_mttr_report(
        self,
        start_date: str,
        end_date: str,
        *args: Sequence,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:

        """Метод для получения отчёта о Mttr за период.
           Метод возвращает дни, без привязки к месяцу.
           Если передать период с 01.05.2022 по 01.07.2022
           вернется отчет за 31 день, процент дня будет средним
           за два месяца.

        Args:
            start_date: дата начала периода.
            end_date: дата конца периода.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        log.debug(
            f"Параметр start_date: {start_date}; " f"Параметр end_date: {end_date}; ",
        )

        _ = {
            "start_date": start_date,
            "end_date": end_date,
        }
        report_kwargs = tuple(_.items())
        return self._get_response(
            TypeReport.MTTR_LEVEL,
            mod_data=report_kwargs,
            mod_params=(),
            **kwargs,
        )

    def get_flr_report(
        self,
        start_date: str,
        end_date: str,
        *args: Sequence,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:

        """Метод для получения отчёта о Flr за период.
           Метод возвращает дни, c привязкой к месяцу.

        Args:
            start_date: дата начала периода.
            end_date: дата конца периода.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        log.debug(
            f"Параметр start_date: {start_date}; " f"Параметр end_date: {end_date}; ",
        )

        _ = {
            "start_date": start_date,
            "end_date": end_date,
        }
        report_kwargs = tuple(_.items())
        return self._get_response(
            TypeReport.FLR_LEVEL,
            mod_data=report_kwargs,
            mod_params=(),
            **kwargs,
        )

    def get_aht_report(
        self,
        start_date: str,
        end_date: str,
        *args: Sequence,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:

        """Метод для получения отчёта о AHT за период.
           Метод возвращает дни, c привязкой к месяцу.

        Args:
            start_date: дата начала периода.
            end_date: дата конца периода.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        log.debug(
            f"Параметр start_date: {start_date}; " f"Параметр end_date: {end_date}; ",
        )

        _ = {
            "start_date": start_date,
            "end_date": end_date,
        }
        report_kwargs = tuple(_.items())
        return self._get_response(
            TypeReport.AHT_LEVEL,
            mod_data=report_kwargs,
            mod_params=(),
            **kwargs,
        )

    def _get_response(
        self,
        report: Union[TypeReport, SearchType],
        mod_params: Union[Tuple[Tuple[str, Any]], Tuple] = (),
        mod_data: Union[Tuple[Tuple[str, Any]], Tuple] = (),
        *args: Sequence,
        **kwargs: Mapping,
    ) -> FORMATTED_RESPONSE:

        """Шаблонный метод для получения ответа от CRM NAUMEN.

        Args:
            report (Union[TypeReport, SearchType]): необходимый отчёт.
            mod_params: (Union[Tuple[Tuple[str, Any]], Tuple]):
            модифицированные параметры запроса
            mod_data: (Union[Tuple[Tuple[str, Any]], Tuple]):
            модифицированный данные запроса
            *args: прокинутые позиционные аргументы.
            **kwargs: прокинутые именнованные аргументы.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        if not self._session:
            log.exception("Ошибка соединения с CRM NAUMEN.")
            error_response = ResponseTemplate(StatusType._UNAUTHORIZED, ())
            error_response.status.description = (
                "You are not authorized " "to get report."
            )
            return make_response(error_response, self.formatter)

        try:
            if report in TypeReport:
                call_func = get_report
            elif report in SearchType:
                call_func = search  # type: ignore

            content = call_func(
                self._session,
                report,  # type: ignore
                *args,
                mod_params=mod_params,
                mod_data=mod_data,
                **kwargs,  # type: ignore
            )
            api_response = ResponseTemplate(StatusType._SUCCESS, content)
            log.debug("Ответ на запрос получен.")
            return make_response(api_response, self.formatter)

        except exceptions.ConnectionError:
            log.exception("Ошибка соединения с CRM NAUMEN.")
            error_response = ResponseTemplate(StatusType._GATEWAY_TIMEOUT, ())
            return make_response(error_response, self.formatter)

        except CantGetData:
            log.exception("Ошибка получения данных из CRM NAUMEN.")
            error_response = ResponseTemplate(StatusType._BAD_REQUEST, ())
            return make_response(error_response, self.formatter)

        except InvalidDate:
            log.exception("Передан не верный формат дыты из CRM NAUMEN.")
            error_response = ResponseTemplate(StatusType._BAD_REQUEST, ())
            error_response.status.description = (
                "Invalid date format. " "Allowed date format: " "%d.%m.%Y"
            )
            return make_response(error_response, self.formatter)

        except ConnectionsFailed:
            log.exception("Ошибка соединения с CRM NAUMEN.")
            error_response = ResponseTemplate(StatusType._UNAUTHORIZED, ())
            return make_response(error_response, self.formatter)


#  TODO
# finded_items_obj = loads(finded_items_json)

# if finded_items_obj["status_code"] != 200:
#     return finded_items_json

# for num, item in enumerate(finded_items_obj["content"]):
#     finded_items_obj["content"][
#         num] = loads(self.get_issue_card(item['uuid']))["content"]
# return finded_items_obj
