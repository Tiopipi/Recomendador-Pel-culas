import pandas as pd

def show_recommendations(recommendations):
    """Muestra las recomendaciones en forma de tabla."""
    if not recommendations:
        print("No se encontraron recomendaciones.")
        return

    if isinstance(recommendations, dict) and "error" in recommendations:
        print(f"Error: {recommendations['error']}")
        return

    df = pd.DataFrame(recommendations)
    if 'recommendation_score' in df.columns:
        df['recommendation_score'] = df['recommendation_score'].apply(lambda x: f"{x:.2f}")
    if 'promedio_valoracion' in df.columns:
        df['promedio_valoracion'] = df['promedio_valoracion'].apply(lambda x: f"{x:.1f}" if x else "N/A")
    if 'generos' in df.columns:
        df['generos'] = df['generos'].apply(lambda x: ", ".join(x) if x else "")
    if 'directores' in df.columns:
        df['directores'] = df['directores'].apply(lambda x: ", ".join(x) if x else "")

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df)