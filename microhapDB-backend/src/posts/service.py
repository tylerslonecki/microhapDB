from sqlalchemy import func, case
from sqlalchemy.future import select
from .models import Sequence, SequenceLog, UploadBatch
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from upsetplot import plot
from matplotlib import pyplot as plt
import base64
from io import BytesIO

async def get_total_unique_sequences(db: AsyncSession):
    result = await db.execute(select(func.count(Sequence.hapid.distinct())))
    return result.scalar()

async def get_new_sequences_for_batch(db: AsyncSession):
    result = await db.execute(select(UploadBatch.id).order_by(UploadBatch.id.desc()))
    last_batch = result.scalars().first()

    if last_batch is None:
        return 0

    result = await db.execute(
        select(func.count(SequenceLog.hapid.distinct()))
        .where(SequenceLog.batch_id == last_batch)
        .where(SequenceLog.was_new == True)
    )
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

async def get_all_batch_summaries(db: AsyncSession):
    try:
        result = await db.execute(
            select(
                UploadBatch.id.label('batch_id'),
                UploadBatch.created_at.label('created_at'),
                func.count(case((SequenceLog.was_new == True, SequenceLog.hapid), else_=None)).label('new_sequences')
            ).outerjoin(
                SequenceLog, UploadBatch.id == SequenceLog.batch_id
            ).group_by(
                UploadBatch.id,
                UploadBatch.created_at
            ).order_by(UploadBatch.id)
        )
        batches = result.all()

        batch_summaries = [
            {"batch_id": batch_id, "date": created_at.strftime('%Y-%m-%d %H:%M:%S'), "new_sequences": new_sequences}
            for batch_id, created_at, new_sequences in batches
        ]

        cumulative_sum = 0
        for summary in batch_summaries:
            cumulative_sum += summary["new_sequences"]
            summary["cumulative_sum"] = cumulative_sum

        return batch_summaries

    except Exception as e:
        print("Error retrieving batch summaries:", str(e))
        return []

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

async def prepare_data_for_upset_plot(db: AsyncSession):
    result = await db.execute(select(SequenceLog.hapID, SequenceLog.batch_id))
    data = result.all()
    df = pd.DataFrame(data, columns=['hapID', 'batch_id'])

    df['presence'] = 1
    df_pivot = df.pivot_table(index='hapID', columns='batch_id', values='presence', fill_value=0, aggfunc='sum').astype(bool)
    df_pivot.columns = df_pivot.columns.map(str)
    return df_pivot

# def prepare_data_for_upset_plot(db):
#     # Fetch data from database
#     data = db.query(SequenceLog.hapID, SequenceLog.batch_id).all()
#     df = pd.DataFrame(data, columns=['hapID', 'batch_id'])
#
#     # Create a presence column for pivot
#     df['presence'] = 1
#     # Pivot to get hapIDs as index and batch_ids as columns with presence as values
#     df_pivot = df.pivot_table(index='hapID', columns='batch_id', values='presence', fill_value=0, aggfunc='sum').astype(bool)
#
#     # Convert the batch_id columns to string types to comply with the UpSetPlot requirement
#     df_pivot.columns = df_pivot.columns.map(str)
#
#     # # Ensure columns are in MultiIndex format
#     # if not isinstance(df_pivot.columns, pd.MultiIndex):
#     #     df_pivot.columns = pd.MultiIndex.from_arrays([df_pivot.columns])
#     print(df_pivot)
#     return df_pivot

async def generate_upset_plot(db: AsyncSession):
    df = await prepare_data_for_upset_plot(db)

    if df.empty:
        return None

    try:
        upset_data = from_memberships(df.itertuples(index=False, name=None), data=len(df) * [1])
        upset = UpSet(upset_data, show_counts='%d')
        upset.plot()
        plt.title('Upset Plot of Sequences')

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plot_base64 = base64.b64encode(image_png).decode('utf-8')

        return plot_base64
    except Exception as e:
        print("Failed to generate upset plot:", str(e))
        return None
# def generate_upset_plot(db):
#     df = prepare_data_for_upset_plot(db)
#
#     counts = [56, 283, 1279, 5882, 24, 90, 429, 1957]
#     from upsetplot import from_memberships
#     upset_data = from_memberships(df, data=counts)
#
#     # if df.empty or not isinstance(df.columns, pd.MultiIndex):
#     #     print("DataFrame is not suitable for upset plotting.")
#     #     return None
#
#     try:
#         # Generate upset plot
#         upset = plot(upset_data, show_counts='%d')
#         plt.title('Upset Plot of Sequences')
#
#         # Save plot to BytesIO and convert to base64
#         buffer = BytesIO()
#         plt.savefig(buffer, format='png')
#         plt.close()
#         buffer.seek(0)
#         image_png = buffer.getvalue()
#         buffer.close()
#         plot_base64 = base64.b64encode(image_png).decode('utf-8')
#
#         return plot_base64
#     except Exception as e:
#         print("Failed to generate upset plot:", str(e))
#         return None

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

async def generate_line_chart(db: AsyncSession):
    summaries = await get_all_batch_summaries(db)

    df = pd.DataFrame(summaries)

    # Print DataFrame columns to debug
    print("DataFrame columns:", df.columns)

    if 'batch_id' not in df.columns:
        raise ValueError("The DataFrame does not contain the 'batch_id' column")

    df['batch_id'] = df['batch_id'].apply(lambda x: f"v{str(x).zfill(3)}")

    plt.figure(figsize=(10, 5))
    plt.plot(df['batch_id'], df['cumulative_sum'], marker='o')
    plt.xlabel('Batch ID')
    plt.ylabel('New Sequences')
    plt.title('Number of New Sequences per Batch')
    plt.grid(True)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = buffer.getvalue()
    buffer.close()
    plt.close()

    plot_base64 = base64.b64encode(plot_data).decode('utf-8')
    return plot_base64

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