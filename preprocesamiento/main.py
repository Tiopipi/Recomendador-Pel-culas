from neo4j import GraphDatabase
import pandas as pd
from collections import defaultdict
import time
import glob
import os
import multiprocessing
from tqdm import tqdm
import concurrent.futures

from similarity_calculator import calculate_similarity_for_user_pair_cy

NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Virt1234*"


def process_csv_file(filename):
    """Procesa un archivo CSV individual y devuelve las valoraciones"""
    try:
        df = pd.read_csv(filename, header=0)
        return [(row['userId'], row['id'], row['rating']) for _, row in df.iterrows()]
    except Exception as e:
        print(f"Error procesando {filename}: {e}")
        return []


class SimilarityCalculator:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "similitudes_csv")
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Los archivos CSV de similitudes se guardarán en: {self.output_dir}")

    def close(self):
        self.driver.close()

    def cargar_valoraciones_desde_csv_parallel(self, csv_pattern, num_processes=None):
        """Carga valoraciones desde archivos CSV usando multiprocessing"""
        print("Buscando archivos CSV...")
        all_files = glob.glob(csv_pattern)
        print(f"Encontrados {len(all_files)} archivos CSV.")

        if not num_processes:
            num_processes = min(multiprocessing.cpu_count(), 8)

        print(f"Utilizando {num_processes} procesos para cargar archivos...")

        with multiprocessing.Pool(processes=num_processes) as pool:
            results = []
            for i, result in enumerate(tqdm(pool.imap_unordered(process_csv_file, all_files),
                                            total=len(all_files),
                                            desc="Procesando archivos")):
                results.extend(result)

        print(f"Total de valoraciones cargadas: {len(results)}")
        return results

    def guardar_similitudes_en_csv(self, similarities, batch_id):
        """Guarda las similitudes calculadas en un archivo CSV"""
        if not similarities:
            return

        csv_filename = os.path.join(self.output_dir, f"similitudes_batch_{batch_id}.csv")

        df = pd.DataFrame(similarities, columns=['usuario1', 'usuario2', 'similitud'])
        df.to_csv(csv_filename, index=False)
        print(f"Guardadas {len(similarities)} similitudes en {csv_filename}")

        return csv_filename

    def calcular_similitudes_por_chunks(self, ratings_data, min_peliculas=3, chunk_size=1000, csv_batch_size=100000,
                                        num_workers=None):
        """Calcula similitudes de coseno entre usuarios procesando por chunks y guardando en CSV - Versión optimizada con Cython"""
        print("Organizando valoraciones por usuario...")
        user_ratings = defaultdict(dict)
        for user_id, movie_id, rating in tqdm(ratings_data, desc="Organizando valoraciones"):
            user_ratings[user_id][movie_id] = rating

        users = list(user_ratings.keys())
        total_users = len(users)
        print(f"Total de usuarios: {total_users}")

        if not num_workers:
            num_workers = min(os.cpu_count() + 4, 16)

        print(f"Utilizando {num_workers} workers para cálculos de similitud")

        csv_files = []
        batch_id = 1
        total_similarities = 0

        for i in range(0, total_users, chunk_size):
            chunk_users = users[i:i + chunk_size]
            chunk_start_time = time.time()
            print(f"Procesando chunk de usuarios {i + 1}-{min(i + chunk_size, total_users)} de {total_users}")

            similarity_pairs = []

            for idx, user1 in enumerate(chunk_users):
                for user2 in users:
                    if user1 >= user2:
                        continue

                    similarity_pairs.append((user1, user2, user_ratings[user1], user_ratings[user2], min_peliculas))

            similarities = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                for result in tqdm(
                        executor.map(calculate_similarity_for_user_pair_cy, similarity_pairs),
                        total=len(similarity_pairs),
                        desc=f"Calculando similitudes en chunk {i // chunk_size + 1}",
                        unit="par"
                ):
                    if result:
                        similarities.append(result)

                        if len(similarities) >= csv_batch_size:
                            csv_file = self.guardar_similitudes_en_csv(similarities, batch_id)
                            csv_files.append(csv_file)
                            total_similarities += len(similarities)
                            similarities = []
                            batch_id += 1

            if similarities:
                csv_file = self.guardar_similitudes_en_csv(similarities, batch_id)
                csv_files.append(csv_file)
                total_similarities += len(similarities)
                similarities = []
                batch_id += 1

            chunk_time = time.time() - chunk_start_time
            print(f"Chunk procesado en {chunk_time:.2f} segundos ({chunk_time / 60:.2f} min)")

        print(f"Procesamiento completado. Total de similitudes calculadas: {total_similarities}")
        return csv_files

    def importar_similitudes_desde_csv_a_neo4j(self, csv_files):
        """Importa las similitudes desde los archivos CSV a Neo4j"""
        print(f"Importando {len(csv_files)} archivos CSV a Neo4j...")

        for i, csv_file in enumerate(csv_files):
            print(f"Procesando archivo {i + 1}/{len(csv_files)}: {os.path.basename(csv_file)}")

            batch_size = 5000
            total_rows = sum(1 for _ in open(csv_file)) - 1

            with tqdm(total=total_rows, desc=f"Importando {os.path.basename(csv_file)}") as pbar:
                for chunk in pd.read_csv(csv_file, chunksize=batch_size):
                    similarities = [(row['usuario1'], row['usuario2'], row['similitud']) for _, row in chunk.iterrows()]

                    self.guardar_similitudes_en_neo4j(similarities, show_progress=False)
                    pbar.update(len(chunk))

        return "Todas las similitudes han sido importadas a Neo4j."

    def guardar_similitudes_en_neo4j(self, similarities, show_progress=True):
        """Guarda las similitudes calculadas en Neo4j"""
        if not similarities:
            return

        if show_progress:
            print(f"Almacenando {len(similarities)} similitudes en Neo4j...")

        batch_size = 1000
        progress_iter = range(0, len(similarities), batch_size)

        if show_progress:
            progress_iter = tqdm(progress_iter, desc="Guardando en Neo4j", unit="batch")

        for i in progress_iter:
            batch = similarities[i:i + batch_size]

            query = """
            UNWIND $batch AS pair
            MATCH (u1:Usuario {id: pair[0]}), (u2:Usuario {id: pair[1]})
            MERGE (u1)-[s:SIMILAR]-(u2)
            SET s.score = pair[2]
            """

            tries = 0
            max_tries = 3
            while tries < max_tries:
                try:
                    with self.driver.session() as session:
                        session.run(query, batch=batch)
                    break
                except Exception as e:
                    tries += 1
                    if tries == max_tries:
                        print(f"Error guardando lote después de {max_tries} intentos: {e}")
                        if batch_size > 100:
                            smaller_batch_size = batch_size // 2
                            print(f"Reintentando con lotes de {smaller_batch_size}...")
                            for j in range(i, min(i + batch_size, len(similarities)), smaller_batch_size):
                                smaller_batch = similarities[j:j + smaller_batch_size]
                                try:
                                    with self.driver.session() as session:
                                        session.run(query, batch=smaller_batch)
                                except Exception as e2:
                                    print(f"Error persistente: {e2}")
                    else:
                        print(f"Intento {tries}/{max_tries} fallido. Reintentando...")
                        time.sleep(1)


def main():
    csv_dir = "/Users/tiopipi/Desktop/formateo_datos/valoraciones_chunks"
    csv_pattern = os.path.join(csv_dir, "valoraciones_part_*.csv")

    calculator = SimilarityCalculator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        start_time = time.time()

        ratings_data = calculator.cargar_valoraciones_desde_csv_parallel(csv_pattern)

        print("\n--- Fase 1: Calculando similitudes y guardando en CSV (optimizado con Cython) ---")
        csv_files = calculator.calcular_similitudes_por_chunks(
            ratings_data,
            min_peliculas=3,
            chunk_size=10,
            csv_batch_size=10000,
            num_workers=None
        )

        fase1_time = time.time()
        print(
            f"Fase 1 completada en {fase1_time - start_time:.2f} segundos ({(fase1_time - start_time) / 60:.2f} minutos).")
        print(f"Se han generado {len(csv_files)} archivos CSV con similitudes.")

        print("\n--- Fase 2: Importando similitudes desde CSV a Neo4j ---")
        calculator.importar_similitudes_desde_csv_a_neo4j(csv_files)

        elapsed = time.time() - start_time
        print(f"Proceso completado en {elapsed:.2f} segundos ({elapsed / 60:.2f} minutos).")
        print(f"- Fase 1 (CSV): {(fase1_time - start_time) / 60:.2f} minutos")
        print(f"- Fase 2 (Neo4j): {(time.time() - fase1_time) / 60:.2f} minutos")

    except Exception as e:
        print(f"Error general: {e}")
    finally:
        calculator.close()


if __name__ == "__main__":
    main()