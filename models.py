class GameParams():
    def __init__(self, level: int=None, time: int=None, time_inc: int=None, side: str=None):  
        """
        :param level: The difficulty level of the game.
        :type level: int
        :param time: The time limit of the game in seconds.  
        :type time: int
        :param time_inc: The increment after each move in seconds.  
        :type time_inc: int
        :param side: The side of the game.  
        :type side: str
        """

        self._level = level
        self._time = time
        self._time_inc = time_inc
        self._side = side

    @property
    def level(self) -> int:
        return self._level

    @level.setter
    def level(self, level: int):
        if level is None:
            raise ValueError("Invalid value for `level`, must not be `None`")  

        self._level = level

    @property
    def time(self) -> int:
        return self._time

    @time.setter
    def time(self, time: int):
        if time is None:
            raise ValueError("Invalid value for `time`, must not be `None`")  

        self._time = time

    @property
    def time_inc(self) -> int:
        return self._time_inc

    @time_inc.setter
    def time_inc(self, time_inc: int):
        if time_inc is None:
            raise ValueError("Invalid value for `time_inc`, must not be `None`")  

        self._time_inc = time_inc

    @property
    def side(self) -> str:
        return self._side

    @side.setter
    def side(self, side: str):
        if side is None:
            raise ValueError("Invalid value for `side`, must not be `None`")  

        self._side = side