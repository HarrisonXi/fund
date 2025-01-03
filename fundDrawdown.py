import pandas as pd

class fundDrawdown:
    
    def __init__(self, df: pd.DataFrame):
        max = 0
        drawdown = []
        for index, row in df.iterrows():
            if row.value >= max:
                max = row.value
                dd = 0
            elif row.value < max:
                dd = (1 - row.value / max) * 100
            drawdown.append(dd)
        self.__df = df.drop(columns = ['value', 'bonus', 'ratio'])
        self.__df['drawdown'] = drawdown

    @property
    def max(self) -> float:
        return self.__df['drawdown'].max()

    @property
    def quantile95(self) -> float:
        return self.__df['drawdown'].quantile(0.95)

    @property
    def quantile9(self) -> float:
        return self.__df['drawdown'].quantile(0.9)