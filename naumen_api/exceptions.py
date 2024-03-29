class ConnectionsFailed(Exception):

    """Исключение возвращяемой при невозможности создать соединение CRM.

    Attributes:

    """

    def __init__(
        self,
        message: str = (
            "Неудалось создать подключение используя "
            "переданные данные. Проверьте данные и "
            "маршрут до системы."
        ),
    ) -> None:
        self.message = message
        super().__init__(self.message)


class CantGetData(Exception):

    """Исключение возвращяемой при невозможности получить данные из CRM.

    Attributes:

    """


class InvalidDate(Exception):

    """Исключение возвращяемой при невозможности получить данные из CRM.

    Attributes:
        message: объяснение ошибки.
    """

    def __init__(
        self,
        message: str = ("Формат даты неверный." "Необходимый формат %d.%m.%Y"),
    ) -> None:
        self.message = message
        super().__init__(self.message)
