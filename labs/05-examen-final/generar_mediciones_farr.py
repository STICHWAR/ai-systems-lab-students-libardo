"""Genera pares biométricos locales para evaluar FAR/FRR sin exponer vectores."""
import argparse
import csv
from pathlib import Path

from biometric_store import BiometricStore
from face_auth import FaceAuthenticator


def generate(user_a: str, user_b: str, output: Path) -> tuple[int, int]:
    store = BiometricStore()
    auth = FaceAuthenticator()
    samples = {user_a: store.load_embedding(user_a), user_b: store.load_embedding(user_b)}
    rows: list[dict[str, str]] = []

    # Cada par no ordenado de una misma persona se cuenta una única vez.
    for user_id, vectors in samples.items():
        for left in range(len(vectors)):
            for right in range(left + 1, len(vectors)):
                score = auth.similarities([vectors[left]], vectors[right])[0]
                rows.append({
                    'par_id': f'genuino:{user_id}:{left}:{right}',
                    'similaridad': f'{score:.8f}',
                    'tipo': 'genuino',
                })

    # Un par cruzado usa una muestra de cada participante y se cuenta una vez.
    for first_index, first in enumerate(samples[user_a]):
        for second_index, second in enumerate(samples[user_b]):
            score = auth.similarities([first], second)[0]
            rows.append({
                'par_id': f'impostor:{user_a}:{first_index}:{user_b}:{second_index}',
                'similaridad': f'{score:.8f}',
                'tipo': 'impostor',
            })

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['par_id', 'similaridad', 'tipo'])
        writer.writeheader()
        writer.writerows(rows)
    genuine = sum(row['tipo'] == 'genuino' for row in rows)
    impostor = sum(row['tipo'] == 'impostor' for row in rows)
    return genuine, impostor


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--usuario-a', default='integrante_1')
    parser.add_argument('--usuario-b', default='integrante_2')
    parser.add_argument('--salida', type=Path, default=Path(__file__).parent / 'rostros' / 'mediciones_farr.csv')
    args = parser.parse_args()
    genuine, impostor = generate(args.usuario_a, args.usuario_b, args.salida)
    print(f'Pares genuinos únicos: {genuine}; pares impostores únicos: {impostor}.')
    print('El archivo queda en almacenamiento local privado; no se imprimen similitudes ni embeddings.')
