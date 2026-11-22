import sqlite3

conexao = sqlite3.connect("foundit.db")
print("id | usuario_id | revogado | expira_em")
for linha in conexao.execute(
    "SELECT id, usuario_id, revogado, expira_em FROM tokens_refresh ORDER BY id"
):
    print(linha)
conexao.close()