import pandas as pd
import numpy as np
from operator import itemgetter


def handle_null(input_data, col, by, impute_type):
    if impute_type.lower() == 'mean':
        output_data = input_data[col].fillna(input_data.groupby(by)[col].mean())
    elif impute_type.lower() == 'min':
        output_data = input_data[col].fillna(input_data.groupby(by)[col].min())
    elif impute_type.lower() == 'max':
        output_data = input_data[col].fillna(input_data.groupby(by)[col].max())

    return output_data


def change_type(df, col, col_type):
    if col_type == str:
        df[col] = df[col].apply(lambda x: str(x))
    elif col_type == int:
        if type(df[col]) == str:
            df[col] = df[col].apply(lambda x: int(x.replace(',','')
                                                .replace(' ','')))
        else:
            df[col] = df[col].apply(lambda x: int(x))
    elif col_type == float:
        if type(df[col]) == str:
            df[col] = df[col].apply(lambda x: float(x.replace(',','')
                                                    .replace(' ','')))
        else:
            df[col] = df[col].apply(lambda x: float(x))
    else:
        print('Type unsupported')
    return df


def data_selection(input_data: pd.DataFrame, cond=None, keep_col=None, drop_col=None, sort_by=None, merge_data=None,
                   merge_by=None, merge_keep_col=None, sort_asc=True, rename=None):
    """
    Return a new dataframe of given filter crateria.

            Parameters
            ----------
            input_data :
            cond : int or tuple of int
                Shape of the empty matrix.
            keep_col : data-type, optional
                Desired output data-type.
            drop_col : {'C', 'F'}, optional
                Whether to store multidimensional data in row-major
                (C-style) or column-major (Fortran-style) order in
                memory.
            sort_by :
            merge_data :
            merge_by :
            merge_keep_col :
            sort_asc :
            rename :

            Returns
            -------
            output_data :
            An array, or list of arrays, each with ``a.ndim >= 1``.
            Copies are made only if necessary.

            See Also
            --------
            atleast_2d, atleast_3d

            Examples
            --------
            >>>
            >>>    # filled with random data

    """

    if cond is not None:
        output_data = input_data.query(cond)
    else:
        output_data = input_data

    if keep_col is not None:
        output_data = output_data.loc[:, keep_col]

    if drop_col is not None:
        output_data.drop(drop_col, axis=1, inplace=True)

    if merge_keep_col is not None:
        merge_data = merge_data.loc[:, merge_keep_col]

    if merge_data is not None:
        output_data = output_data.merge(merge_data, on=merge_by, how="left")

    if sort_by is not None:
        output_data.sort_values(by=sort_by, ascending=sort_asc, inplace=True)

    if rename is not None:
        output_data.rename(columns=rename, inplace=True)

    return output_data


def derive_baseline(input_data, base_visit, by: list, value, chg=True, pchg=True, ):
    combine_col = by + [value]
    baseline = data_selection(keep_col=combine_col, input_data=input_data,
                              cond=base_visit, rename={value: "BASE"})

    output_data = data_selection(input_data=input_data, merge_data=baseline, merge_by=by)
    if chg:
        output_data["CHG"] = output_data[value]-output_data["BASE"]
    if pchg:
        output_data["PCHG"] = (output_data[value]-output_data["BASE"])/output_data["BASE"]

    return output_data


def derive_extreme_flag(input_data, by_vars: list, sort_var: list, new_var, mode, value_var=None):
    if mode.lower() == "last":
        temp = input_data.sort_values(sort_var).groupby(by_vars).last()
    elif mode.lower() == "first":
        temp = input_data.sort_values(sort_var).groupby(by_vars).first()
    elif mode.lower() == "max":
        temp = input_data.loc[input_data.sort_values(sort_var).groupby(by_vars)[value_var].idxmax(), :]
    elif mode.lower() == "min":
        temp = input_data.loc[input_data.sort_values(sort_var).groupby(by_vars)[value_var].idxmin(), :]
    temp[new_var] = "Y"
    output_data = data_selection(input_data, merge_data=temp.reset_index(), merge_by=by_vars+sort_var,
                                 merge_keep_col=by_vars+sort_var+new_var.split())

    return output_data


def time_to_event(input_data, start_date, end_date, censor_date, new_var, unit):
    output_data = input_data.astype({start_date: 'datetime64[ns]', end_date: 'datetime64[ns]',
                                     censor_date: 'datetime64[ns]'})

    output_data[new_var] = np.where((output_data[start_date].notnull()) & (output_data[end_date].notnull()),
                                    output_data[end_date] - output_data[start_date],
                                    output_data[censor_date] - output_data[start_date])
    output_data['censor_status'] = np.where((output_data[start_date].notnull()) & (output_data[end_date].notnull()), 1, 0)

    if unit.lower() == 'day':
        output_data[new_var] = output_data[new_var].dt.days
    elif unit.lower() == 'week':
        output_data[new_var] = round(output_data[new_var].dt.days/7, 2)
    elif unit.lower() == 'month':
        output_data[new_var] = round(output_data[new_var].dt.days/30, 2)
    elif unit.lower() == 'year':
        output_data[new_var] = round(output_data[new_var].dt.days/365.25, 2)
    output_data['unit'] = unit

    return output_data


def read(path, source, sheet_name = None, table = False, sql = None, con = None):
    df = None
    if source == 'csv':
        df = pd.read_csv(path)   
    elif source == 'tsv':
        df = pd.read_csv(path, sep='\t')    
    elif source == 'excel':
        if sheet_name is None:
            df = pd.read_excel(path)  
        else:
            df = pd.read_excel(io=path, sheet_name = sheet_name)
    elif source == 'json':
        df = pd.read_json(path)
    elif source == 'html':
        df = pd.read_html(path)
    elif source == 'xml':
        df = pd.read_spss(path)
    elif source = 'sql' and name is not None and con is not None:
        pandas.read_sql(sql, con)
    else: 
        print("Source type not supported")
    return df


def check_bias(df, col = None, real_dist = None, marg = 5):
    nul = df.isna().sum()
    too_nul = []
    leng = df.shape[0]
    i = 0
    for n in nul:
        if n >= 0.1 * leng:
            too_nul.append([dat.columns[i], n])
        i += 1
    print('columns with too many null values: ', too_nul)
    if real_dist is not None and col is not None:
        count = df[col].value_counts(ascending=False).rename_axis(
            'vals').reset_index(name='dist')
        count.index.name = 'Index'
        count['dist'] = count['dist']*100/len(df)
        skew = []
        for i in range(0,len(real_dist)):
            dist = count.loc[count['vals'] == real_dist[i][0]]
            real = real_dist[i][1]
            ours = dist['dist'].values[0]
            print(str(ours) + " "+ str(real))
            if ours > (real + marg) or ours < (real - marg):
                skew.append(dist)
        print(skew)


def numeric_to_categorical(df, col: str, bounds, add = False):
    def group (row, bounds, col):
        bounds = sorted(bounds, key=itemgetter(0))
        for i in bounds:
            if float(row[col]) <= i[0]:
                return i[1]
    if add == True:
        name = col+'_group'
        df[name] = df.apply(lambda row: group(row, bounds, col), axis=1)
        return df
    else:
        df[col] = df.apply(lambda row: group(row, bounds, col), axis=1)
        return df
