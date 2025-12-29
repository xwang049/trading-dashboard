#%%
import CSDataAPI
import pandas as pd

'''
    Before using scripts below, ensure that:
    1) Python package pyzmq is installed. <pip install pyzmq>
    2) Curveseries Python Package is downloaded and saved:
        -Package can be downloaded at: https://www.curve-series.com/data-api
        -Package is recommended to be saved in:
            <C:\\Users\\{user}\\AppData\\Local\\Programs\\Python\\{Python-Version}\\Lib>
            or where the Libraries are of Python is stored at.
'''
#%%
def CS_Data_API(equation, start_date,end_date):
    '''
    CS Data API
    *Requires Curveseries Desktop to be logged in
    Takes in 3 Parameters:
        equation: equation to be queried
        start_date: start date in format 'dd-mmm-yyyy' or '%d-%b-%Y'
        end_date: end date in format 'dd-mmm-yyyy' or '%d-%b-%Y'
    Returns a dataframe
    '''
    result = CSDataAPI.getCSData(equation,start_date,end_date)
    print('Result Gotten from API')
    df = pd.DataFrame(result)
    return df

def CS_Data_API_Curve(equation,curve_date,end_date):
    '''
    CS Data API
    *Requires Curveseries Desktop to be logged in
    Takes in 3 Parameters:
        equation: equation to be queried
        start_date: start date in format 'dd-mmm-yyyy' or '%d-%b-%Y'
        end_date: end date in format 'dd-mmm-yyyy' or '%d-%b-%Y'
    Returns a dataframe
    '''
    result = CSDataAPI.getCSCurve(equation, curve_date,end_date)
    print('Result Gotten from API')
    df = pd.DataFrame(result)
    return df

def CS_Data_API_Dict(dictionary,start_date,end_date):
    '''
    CS Data API
    *Requires Curveseries Desktop to be logged in
    Takes in 3 Parameters:
        dictionary: dictionary of equation to be queried
            For example:
                crude_oil ={
                    'Nymex_Crude' : 'roll_contract(NYMEX_Crude_Futures_2020F.Settle,"2Z")',
                    'Brent_Crude' : 'roll_contract(ICE_Brent_Futures_2012F.Settle,"2Z")'
                }
        start_date: start date in format 'dd-mmm-yyyy' or '%d-%b-%Y'
        end_date: end date in format 'dd-mmm-yyyy' or '%d-%b-%Y'
    Returns a dictionary of dataframes
    '''
    results_dict = {}
    for i in enumerate(dictionary):
        #Setting up the Parameters
        equation = dictionary[i[1]]
        result = CSDataAPI.getCSData(equation,start_date,end_date)
        df = pd.DataFrame(result)
        results_dict[i[1]] = df
    return results_dict

#%%
#Example Code
#CS_Data_API for single pull of equation. Below example shows an iteration thru a list
eqn = ['roll_month(Swap_GO_10_EW_2020F.Close,"1")']
for eq in eqn:
    print(CS_Data_API(eq,'01-Jul-2023','08-Aug-2025'))

#%%
#CS_Data_API_Curve for single pull of equation for Forward Curves. Below example shows an iteration thru a list
eqn = ['Swap_SGO_10_FP.Close']
curve_date = 'Latest()'
end_date = ''
for eq in eqn:
    print(CS_Data_API_Curve(eq,curve_date,end_date))

#%%
#CS_Data_API_Dict uses a dictionary to extract data in form of dataframe and returning them in a dictionary named with the same key
crude_oil ={
    'Nymex_Crude' : 'roll_contract(NYMEX_Crude_Futures_2020F.Settle,"2Z")',
    'Brent_Crude' : 'roll_contract(ICE_Brent_Futures_2012F.Settle,"2Z")'
}
print(CS_Data_API_Dict(crude_oil,'01-Jan-2023','01-Sep-2023'))

# %%
