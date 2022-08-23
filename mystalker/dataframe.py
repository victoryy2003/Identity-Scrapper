
import os
import pandas as pd

from datetime import datetime, timedelta

from .path import Path
from .state import State
from .district import District
from .school import School

PATH = Path().user_data_dir

class DataFrame:

    def __init__(self) -> None:
        pass

    def pull_csv(self,
                  file_name: str = 'DataBase.csv',
                  dtype: type = str,
                  ignore_validation: bool = False,
                  days_ago: int = 1
                  ) -> pd.DataFrame | pd.Series:
        '''Read dataframe from csv file.
        '''

        try:
            FULL_PATH = os.path.join(PATH, file_name)

            if (datetime.utcfromtimestamp(os.path.getmtime(FULL_PATH)) < datetime.utcnow() - timedelta(days = days_ago)
                and ignore_validation is False
                and file_name == 'DataBase.csv'
                ):
                self.pull_latest_database(
                    push_csv = True
                )

            df = pd.read_csv(
                FULL_PATH,
                dtype = dtype
                )

        except FileNotFoundError:
            if file_name == 'DataBase.csv':
                df = self.pull_latest_database(
                    push_csv = True
                    )

            else:
                return pd.DataFrame()

        return df

    def push_csv(self,
                  dataframe: pd.DataFrame,
                  file_name: str,
                  concat: bool = True,
                  verify_integrity: bool = True,
                  ) -> None:
        '''Push dataframe to csv file.
        '''

        if concat is True and file_name != 'DataBase.csv':
            old_df = self.pull_csv(
                file_name = file_name,
                )

            dataframe = pd.concat(
                [old_df, dataframe],
                verify_integrity = verify_integrity,
                ignore_index = True,
                ).drop_duplicates()

        if file_name in ('DataBase.csv', 'Students.csv'):
            dataframe.sort_values(by = ['State Code', 'District Code', 'School Code'], inplace = True)

        dataframe.to_csv(
            os.path.join(PATH, file_name),
            index = False
            )


    def pull_latest_database(self,
                    push_csv: bool = False,
                    ) -> pd.DataFrame | pd.Series:
        '''Update the database with latest data.
        '''

        df = pd.DataFrame()
        states = State.pull_latest()
        for state_code in states[0]:
            state_code = str(state_code) # Initially it is an int.
            districts = District.pull_latest(state_code)
            for district_code in districts[0]:
                schools = School.pull_latest(state_code, district_code)

                length = len(schools[0])

                for i in range(length):
                    df_temp = pd.DataFrame(
                        {
                            'State Code': [state_code],
                            'State Name': [states[1][states[0].index(state_code)]],
                            'District Code': [district_code],
                            'District Name': [districts[1][districts[0].index(district_code)]],
                            'School Code': [schools[0][i]],
                            'School Name': [schools[1][schools[0].index(schools[0][i])]],
                            }
                        )

                    df = pd.concat([df, df_temp])

        if push_csv is True:
            self.push_csv(df, 'DataBase.csv')

        return df
