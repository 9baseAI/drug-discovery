from admet_ai import ADMETModel
from langchain_core.tools import tool

model = ADMETModel()


@tool
def admet_tools(input: str):
    """
    Predicts ADMET properties for a chemical compound using its SMILES string.
    Input: SMILES string representing the chemical structure.
    Returns:ADMET info .
    """

    preds = model.predict(smiles=input)
    IMPORTANT_ADMET_KEYS = [
        'molecular_weight',
        'logP',
        'hydrogen_bond_acceptors',
        'hydrogen_bond_donors',
        'QED',
        'tpsa',
        'AMES',
        'hERG',
        'ClinTox',
        'Clearance_Hepatocyte_AZ',
        'Half_Life_Obach'
    ]

    filtered_preds = {key: preds.get(key, None) for key in IMPORTANT_ADMET_KEYS}
    return filtered_preds
