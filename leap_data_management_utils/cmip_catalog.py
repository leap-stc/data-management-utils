import pandas as pd

# TODO: This should live in pangeo-forge-esgf?
# Need to test over there if the changes regarding member_id/varaint_label are correct
# are breaking anything. 
# from pangeo_forge_esgf.utils import CMIP6_naming_schema_official
CMIP6_naming_schema_official = 'mip_era.activity_id.institution_id.source_id.experiment_id.member_id.table_id.variable_id.grid_label.version'



def _maybe_prepend_dummy_dcpp(s: str):
    if not "-" in s:
        return "none-" + s
    else:
        return s

def bq_df_to_intake_esm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    iid_facets = CMIP6_naming_schema_official.split(".")
    
    # some legit pandas magic here: https://stackoverflow.com/a/39358924
    df_out = df["instance_id"].str.split(".", expand=True)
    df_out = df_out.rename(columns={i:f for i,f in enumerate(iid_facets)})
    df_out['zstore'] = df['store']
    df_out[["sub_experiment_id", "variant_label"]] = (df_out["member_id"].apply(lambda s: _maybe_prepend_dummy_dcpp(s)).str.split("-", expand=True))
    # df.replace('dummy', np.nan, inplace=True)
    # order the columns in the order of the old csv (not sure if this is necessary)
    df_out = df_out[
        [
            "activity_id",
            "institution_id",
            "source_id",
            "experiment_id",
            "member_id",
            "table_id",
            "variable_id",
            "grid_label",
            "sub_experiment_id",
            "variant_label",
            "version",
            "zstore",
        ]
    ]
    return df_out

def _maybe_join(iterable):
    assert len(iterable) == 2 
    sub_experiment_id = iterable.iloc[0]
    variant_label = iterable.iloc[1]
    if sub_experiment_id != 'none':
        return f"{sub_experiment_id}-{variant_label}"
    else:
        return variant_label

def intake_esm_df_to_bq_df(df: pd.DataFrame) -> pd.DataFrame:
    # now remove the ones already in the pangeo catalog
    df = df.copy()
    df['member_id'] = df[["sub_experiment_id", "variant_label"]].agg(_maybe_join, axis=1)
    df['version'] = 'v'+df['version'].astype(str)
    df['instance_id'] = df[['activity_id', 'institution_id', 'source_id', 'experiment_id',
        'member_id', 'table_id', 'variable_id', 'grid_label', 'version']].astype(str).agg('.'.join, axis=1).tolist()
    df['instance_id'] = 'CMIP6.'+df['instance_id']
    df['store'] = df['zstore']
    # add current time as bigquery timestamp
    df['timestamp'] = pd.Timestamp.now(tz='UTC')
    df = df[['instance_id','store', 'timestamp']]
    return df