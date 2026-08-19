# Adikus Backgammon iPhone Analyzer — fixed build

The previous deployment failed because `requirements.txt` specified
`gnubg-nn>=1.1.0`, while the published release is the pre-release
`1.1.0a8`. Normal `>=1.1.0` does not match a pre-release, so pip reported
"No matching distribution found".

This version pins the actual release:

`gnubg-nn==1.1.0a8`

The app analyzes each new screenshot independently and uses
`gnubg_nn.best_move()` after position validation.

Replace the existing `requirements.txt` and `app.py` in your GitHub repository
with the files in this ZIP. Streamlit Community Cloud should then rebuild the
existing app.
