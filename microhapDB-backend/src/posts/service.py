from collections import Counter

from sqlalchemy import func, case
from sqlalchemy.future import select
from .models import Sequence, SequenceLog, UploadBatch, SequencePresence, Program
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from upsetplot import from_memberships, UpSet
from matplotlib import pyplot as plt
import base64
from io import BytesIO

async def get_total_unique_sequences(db: AsyncSession, species: str):
    query = select(func.count(Sequence.hapid.distinct()))
    if species != 'all':
        query = query.where(Sequence.species == species)
    result = await db.execute(query)
    return result.scalar()



async def get_new_sequences_for_batch(db: AsyncSession, species: str):
    subquery = (
        select(UploadBatch.id)
        .join(SequenceLog, UploadBatch.id == SequenceLog.batch_id)
    )
    if species != 'all':
        subquery = subquery.where(SequenceLog.species == species)
    subquery = subquery.order_by(UploadBatch.id.desc()).limit(1)

    result = await db.execute(subquery)
    last_batch = result.scalar()

    if last_batch is None:
        return 0

    count_query = (
        select(func.count(SequenceLog.hapid.distinct()))
        .where(SequenceLog.batch_id == last_batch)
        .where(SequenceLog.was_new == True)
    )
    if species != 'all':
        count_query = count_query.where(SequenceLog.species == species)
    result = await db.execute(count_query)
    new_sequences_count = result.scalar()
    return new_sequences_count




#
# def get_new_sequences_for_batch(db, batch_id: int = None):
#     # If no batch_id is provided, fetch the most recent batch's ID
#     if batch_id is None:
#         last_batch = db.query(UploadBatch.id).order_by(UploadBatch.id.desc()).first()
#         batch_id = last_batch.id if last_batch else None
#
#     # If there's no batch found in the database, return 0 or handle it as needed
#     if batch_id is None:
#         return 0  # Or raise an error, or return an empty list, etc.
#
#     # Fetch the count of new unique sequences for the given batch
#     return db.query(func.count(SequenceLog.hapID.distinct())).filter(
#         SequenceLog.batch_id == batch_id,
#         SequenceLog.was_new == True
#     ).scalar()

async def get_all_batch_summaries(db: AsyncSession, species: str):
    try:
        if species != 'all':
            # Query batches for a single species
            query = (
                select(
                    UploadBatch.version.label('version'),
                    UploadBatch.created_at.label('created_at'),
                    func.count(
                        case((SequenceLog.was_new == True, SequenceLog.hapid), else_=None)
                    ).label('new_sequences')
                )
                .join(SequenceLog, UploadBatch.id == SequenceLog.batch_id)
                .where(UploadBatch.species == species)
                .group_by(UploadBatch.version, UploadBatch.created_at)
                .order_by(UploadBatch.version)
            )
            result = await db.execute(query)
            batches = result.fetchall()

            batch_summaries = [
                {
                    "version": batch.version,
                    "date": batch.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "new_sequences": batch.new_sequences
                }
                for batch in batches
            ]

            # Calculate cumulative sum
            cumulative_sum = 0
            for summary in batch_summaries:
                cumulative_sum += summary["new_sequences"]
                summary["cumulative_sum"] = cumulative_sum

            return batch_summaries

        else:
            # Query batches for all species
            query = (
                select(
                    UploadBatch.species.label('species'),
                    UploadBatch.version.label('version'),
                    UploadBatch.created_at.label('created_at'),
                    func.count(
                        case((SequenceLog.was_new == True, SequenceLog.hapid), else_=None)
                    ).label('new_sequences')
                )
                .join(SequenceLog, UploadBatch.id == SequenceLog.batch_id)
                .group_by(UploadBatch.species, UploadBatch.version, UploadBatch.created_at)
                .order_by(UploadBatch.species, UploadBatch.version)
            )
            result = await db.execute(query)
            batches = result.fetchall()

            species_data = {}
            for batch in batches:
                sp = batch.species
                if sp not in species_data:
                    species_data[sp] = []
                species_data[sp].append({
                    "version": batch.version,
                    "date": batch.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "new_sequences": batch.new_sequences
                })

            # Calculate cumulative sums for each species
            for sp, summaries in species_data.items():
                cumulative_sum = 0
                for summary in summaries:
                    cumulative_sum += summary["new_sequences"]
                    summary["cumulative_sum"] = cumulative_sum

            return species_data

    except Exception as e:
        print("Error retrieving batch summaries:", str(e))
        return {}





# def get_all_batch_summaries(db):
#     try:
#         # Adjust the query to conditionally count new sequences and order by batch_id
#         batches = db.query(
#             UploadBatch.id.label('batch_id'),
#             UploadBatch.created_at.label('created_at'),
#             func.count(case((SequenceLog.was_new == True, SequenceLog.hapID), else_=None)).label('new_sequences')
#         ).outerjoin(
#             SequenceLog, UploadBatch.id == SequenceLog.batch_id
#         ).group_by(
#             UploadBatch.id,
#             UploadBatch.created_at
#         ).order_by(UploadBatch.id).all()
#
#         # Debug: Print the raw query result
#         print("Query Results:", batches)
#
#         # Create a structured response from the query result
#         batch_summaries = [
#             {"batch_id": batch_id, "date": created_at.strftime('%Y-%m-%d %H:%M:%S'), "new_sequences": new_sequences}
#             for batch_id, created_at, new_sequences in batches
#         ]
#
#         # Add cumulative sum
#         cumulative_sum = 0
#         for summary in batch_summaries:
#             cumulative_sum += summary["new_sequences"]
#             summary["cumulative_sum"] = cumulative_sum
#
#         return batch_summaries
#
#     except Exception as e:
#         # Handle errors and exceptions
#         print("Error retrieving batch summaries:", str(e))
#         return []

async def prepare_data_for_upset_plot(db: AsyncSession, species: str):
    query = (
        select(SequencePresence.hapid, Project.name)
        .join(Project, Project.id == SequencePresence.project_id)
    )
    if species != 'all':
        query = query.where(SequencePresence.species == species)
    result = await db.execute(query)
    data = result.fetchall()
    df = pd.DataFrame(data, columns=['hapid', 'project_name'])

    # Drop duplicates to ensure each hapid-project pair is unique
    df = df.drop_duplicates()

    # Group by hapid and collect the set of project names
    grouped = df.groupby('hapid')['project_name'].apply(lambda x: tuple(sorted(set(x))))

    # Collect the list of memberships
    memberships = grouped.tolist()

    return memberships








async def generate_upset_plot(db: AsyncSession, species: str):
    memberships = await prepare_data_for_upset_plot(db, species)
    if not memberships:
        print("No memberships data available for upset plot.")
        return None

    try:
        # Use Counter to aggregate memberships
        counter = Counter(memberships)
        upset_data = pd.Series(counter)

        # Debugging: Print the first few entries to ensure uniqueness
        print("UpSet Data Sample:", upset_data.head())

        # Create the UpSet plot with subset_size set to None
        upset = UpSet(upset_data, show_counts='%d', subset_size=None)
        upset.plot()
        plt.suptitle('Upset Plot of Sequences by Projects', fontsize=12, color='#00796b')

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plot_base64 = base64.b64encode(image_png).decode('utf-8')

        return plot_base64
    except Exception as e:
        print("Failed to generate upset plot:", str(e))
        return None






async def generate_bar_chart(db: AsyncSession):
    batch_history = await get_all_batch_summaries(db)

    batch_ids = [str(batch['batch_id']) for batch in batch_history]
    cumulative_sums = [batch['cumulative_sum'] for batch in batch_history]

    plt.figure(figsize=(10, 5))
    plt.bar(batch_ids, cumulative_sums, color='skyblue')
    plt.xlabel('Batch ID')
    plt.ylabel('Cumulative Number of Unique Sequences')
    plt.title('Cumulative Number of Unique Sequences with Each Batch')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plot_base64 = base64.b64encode(image_png).decode('utf-8')
    plt.close()

    return plot_base64

# def generate_bar_chart(db):
#     batch_history = get_all_batch_summaries(db)
#
#     # Extract data for the bar chart
#     batch_ids = [str(batch['batch_id']) for batch in batch_history]
#     cumulative_sums = [batch['cumulative_sum'] for batch in batch_history]
#
#     # Plot the bar chart
#     plt.figure(figsize=(10, 5))
#     plt.bar(batch_ids, cumulative_sums, color='skyblue')
#     plt.xlabel('Batch ID')
#     plt.ylabel('Cumulative Number of Unique Sequences')
#     plt.title('Cumulative Number of Unique Sequences with Each Batch')
#
#     # Save plot to buffer
#     buffer = BytesIO()
#     plt.savefig(buffer, format='png')
#     buffer.seek(0)
#     image_png = buffer.getvalue()
#     buffer.close()
#
#     # Convert to base64
#     plot_base64 = base64.b64encode(image_png).decode('utf-8')
#     plt.close()
#
#     return plot_base64

import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64


async def generate_line_chart(db: AsyncSession, species: str):
    if species != 'all':
        summaries = await get_all_batch_summaries(db, species)
        df = pd.DataFrame(summaries)

        if 'version' not in df.columns or df.empty:
            return None  # No data available

        df['version_label'] = df['version'].apply(lambda x: f"V{str(x).zfill(3)}")

        fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
        ax.plot(df['version_label'], df['cumulative_sum'], marker='o', linestyle='-', color='#00796b', linewidth=2, markersize=4)

        ax.set_xlabel('Version', fontsize=10, labelpad=8, color='#333')
        ax.set_ylabel('Cumulative Sequences', fontsize=10, labelpad=8, color='#333')
        ax.set_title(f'Cumulative Sequences per Version - {species.capitalize()}', fontsize=12, pad=10, color='#00796b')

        ax.tick_params(axis='x', labelsize=8, rotation=45, colors='#333')
        ax.tick_params(axis='y', labelsize=8, colors='#333')

        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plot_data = buffer.getvalue()
        buffer.close()
        plt.close()

        plot_base64 = base64.b64encode(plot_data).decode('utf-8')
        return plot_base64
    else:
        summaries = await get_all_batch_summaries(db, species)

        if not summaries:
            return None

        line_charts = {}
        for sp, data in summaries.items():
            df = pd.DataFrame(data)
            if 'version' not in df.columns or df.empty:
                continue

            df['version_label'] = df['version'].apply(lambda x: f"V{str(x).zfill(3)}")

            fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
            ax.plot(df['version_label'], df['cumulative_sum'], marker='o', linestyle='-', color='#00796b', linewidth=2, markersize=4)

            ax.set_xlabel('Version', fontsize=8, labelpad=8, color='#333')
            ax.set_ylabel('Cumulative Sequences', fontsize=8, labelpad=8, color='#333')
            ax.set_title(f'{sp.capitalize()}', fontsize=10, pad=10, color='#00796b')

            ax.tick_params(axis='x', labelsize=6, rotation=45, colors='#333')
            ax.tick_params(axis='y', labelsize=6, colors='#333')

            ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
            plt.tight_layout()

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            plot_data = buffer.getvalue()
            buffer.close()
            plt.close()

            plot_base64 = base64.b64encode(plot_data).decode('utf-8')
            line_charts[sp] = plot_base64

        return line_charts

async def generate_line_chart_data(db: AsyncSession, species: str):
    if species != 'all':
        summaries = await get_all_batch_summaries(db, species)
        if not summaries:
            return None  # No data available

        df = pd.DataFrame(summaries)
        if 'version' not in df.columns or df.empty:
            return None  # No data available

        df['version_label'] = df['version'].apply(lambda x: f"V{str(x).zfill(3)}")

        chart_data = {
            'labels': df['version_label'].tolist(),
            'cumulative_sums': df['cumulative_sum'].tolist(),
        }

        return chart_data
    else:
        summaries = await get_all_batch_summaries(db, species)
        if not summaries:
            return None

        chart_data = {}
        for sp, data in summaries.items():
            df = pd.DataFrame(data)
            if 'version' not in df.columns or df.empty:
                continue

            df['version_label'] = df['version'].apply(lambda x: f"V{str(x).zfill(3)}")

            chart_data[sp] = {
                'labels': df['version_label'].tolist(),
                'cumulative_sums': df['cumulative_sum'].tolist(),
            }

        return chart_data



# def generate_line_chart(db):
#     # Get batch summaries
#     summaries = get_all_batch_summaries(db)
#
#     # Create a DataFrame from summaries
#     df = pd.DataFrame(summaries)
#
#     # Convert batch IDs to string with "v" prefix
#     df['batch_id'] = df['batch_id'].apply(lambda x: f"v{str(x).zfill(3)}")
#
#     # Generate the scatter plot with connected lines
#     plt.figure(figsize=(10, 5))
#     plt.plot(df['batch_id'], df['cumulative_sum'], marker='o')
#     plt.xlabel('Batch ID')
#     plt.ylabel('New Sequences')
#     plt.title('Number of New Sequences per Batch')
#     plt.grid(True)
#
#     # Save plot to BytesIO
#     buffer = BytesIO()
#     plt.savefig(buffer, format='png')
#     buffer.seek(0)
#     plot_data = buffer.getvalue()
#     buffer.close()
#     plt.close()
#
#     # Convert plot to base64 for embedding in HTML
#     plot_base64 = base64.b64encode(plot_data).decode('utf-8')
#     return plot_base64