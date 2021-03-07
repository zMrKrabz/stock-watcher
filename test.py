import pandas as pd
import numpy as np
from datetime import datetime

candles = [
    {'t': 1614879900, 'o': 120.8, 'h': 120.88, 'l': 120, 'c': 120.42, 'v': 90963}, 
    {'t': 1614880800, 'o': 120.43, 'h': 120.66, 'l': 119.845, 'c': 119.85, 'v': 48064}, 
    {'t': 1614881700, 'o': 119.845, 'h': 120.535, 'l': 119.68, 'c': 120.52, 'v': 54977}, 
    {'t': 1614882600, 'o': 120.54, 'h': 120.54, 'l': 119.83, 'c': 119.94, 'v': 48901}, 
    {'t': 1614883500, 'o': 119.86, 'h': 119.995, 'l': 118.695, 'c': 118.74, 'v': 80076}, 
    {'t': 1614884400, 'o': 118.78, 'h': 119.68, 'l': 118.63, 'c': 119.52, 'v': 74566}, 
    {'t': 1614885300, 'o': 119.49, 'h': 120.43, 'l': 119.16, 'c': 120.15, 'v': 86045}, 
    {'t': 1614886200, 'o': 120.23, 'h': 120.52, 'l': 119.85, 'c': 120.52, 'v': 55898}, 
    {'t': 1614887100, 'o': 120.5, 'h': 120.83, 'l': 120.04, 'c': 120.31, 'v': 49665}, 
    {'t': 1614888000, 'o': 120.31, 'h': 120.48, 'l': 119.61, 'c': 119.88, 'v': 51087}, 
    {'t': 1614888900, 'o': 119.83, 'h': 120.115, 'l': 119.525, 'c': 119.955, 'v': 35607}, 
    {'t': 1614889800, 'o': 119.925, 'h': 120.265, 'l': 119.595, 'c': 120.22, 'v': 83414}, 
    {'t': 1614890700, 'o': 120.145, 'h': 120.39, 'l': 119.69, 'c': 120.12, 'v': 114540}, 
    {'t': 1614949200, 'o': 120.3, 'h': 0, 'l': 0, 'c': 0, 'v': 286}, 
    
    {'t': 1614954600, 'o': 120.96, 'h': 121.535, 'l': 119.49, 'c': 119.95, 'v': 133302},
    {'t': 1614955500, 'o': 119.97, 'h': 120.27, 'l': 118.62, 'c': 119.1, 'v': 105146}, 
    {'t': 1614956400, 'o': 119.13, 'h': 119.985, 'l': 118.78, 'c': 118.805, 'v': 72774}, 
    {'t': 1614957300, 'o': 118.85, 'h': 119.39, 'l': 118.66, 'c': 118.77, 'v': 55302}, 
    {'t': 1614958200, 'o': 118.83, 'h': 119.4, 'l': 118.41, 'c': 119.075, 'v': 103989}, 
    {'t': 1614959100, 'o': 119.04, 'h': 119.8, 'l': 118.78, 'c': 118.93, 'v': 70702}, 
    {'t': 1614960000, 'o': 118.96, 'h': 119.315, 'l': 118.295, 'c': 118.295, 'v': 71000},
    {'t': 1614960900, 'o': 118.32, 'h': 118.42, 'l': 117.575, 'c': 117.735, 'v': 76606}, 
    {'t': 1614961800, 'o': 117.82, 'h': 118.585, 'l': 117.8, 'c': 118.46, 'v': 109939}, 
    {'t': 1614962700, 'o': 118.44, 'h': 119.07, 'l': 117.855, 'c': 119.02, 'v': 111995}, 
    {'t': 1614963600, 'o': 119.04, 'h': 119.085, 'l': 118.585, 'c': 118.74, 'v': 131860}, 
    {'t': 1614964500, 'o': 118.685, 'h': 119.575, 'l': 118.655, 'c': 119.42, 'v': 95086}, 
    {'t': 1614965400, 'o': 119.41, 'h': 119.65, 'l': 118.85, 'c': 119.57, 'v': 66804}, 
    {'t': 1614966300, 'o': 119.535, 'h': 119.715, 'l': 119.02, 'c': 119.2, 'v': 48228}, 
    {'t': 1614967200, 'o': 119.18, 'h': 119.335, 'l': 118.48, 'c': 119.305, 'v': 54790},
    {'t': 1614968100, 'o': 119.29, 'h': 119.99, 'l': 119.225, 'c': 119.935, 'v': 111464}, 
    {'t': 1614969000, 'o': 119.945, 'h': 120.67, 'l': 119.89, 'c': 120.29, 'v': 86121}, 
    {'t': 1614969900, 'o': 120.3, 'h': 120.51, 'l': 119.9, 'c': 120.28, 'v': 38329},
    {'t': 1614970800, 'o': 120.29, 'h': 120.42, 'l': 119.82, 'c': 120.015, 'v': 42692},
    {'t': 1614971700, 'o': 120.105, 'h': 120.5, 'l': 119.66, 'c': 120.485, 'v': 52257},
    {'t': 1614972600, 'o': 120.49, 'h': 121.075, 'l': 120.5, 'c': 120.8, 'v': 50198}, 
    {'t': 1614973500, 'o': 120.81, 'h': 121.46, 'l': 120.69, 'c': 121.34, 'v': 45612},
    {'t': 1614974400, 'o': 121.345, 'h': 121.55, 'l': 120.87, 'c': 121.11, 'v': 49516}, 
    {'t': 1614975300, 'o': 121.12, 'h': 121.43, 'l': 120.92, 'c': 121.215, 'v': 70847}, 
    {'t': 1614976200, 'o': 121.25, 'h': 121.64, 'l': 121.15, 'c': 121.36, 'v': 66887}, 
    {'t': 1614977100, 'o': 121.335, 'h': 121.93, 'l': 121.04, 'c': 121.4, 'v': 134728}
]

df = pd.DataFrame(candles)
df["Datetime"] = pd.to_datetime(df["t"], unit="s")
sample = df.resample("1H", on="Datetime")

aggregated = sample.agg(
    {
        "t": "first",
        "o": "first",
        "h": "max",
        "l": "min",
        "c": "last",
        "v": "sum",
    }
)
df = aggregated[aggregated["t"].notna()]
record = df.to_dict('records')
print(record)
# for name, group in sample:
#     print(name)
#     print(group)