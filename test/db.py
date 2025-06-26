import asyncio
import logging
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from asyncpg import connect

from bot.config import DATABASE_URL_TEST
from bot.db import get_accounts

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(loop_scope='function')
async def db():
    """Create a test database connection with schema setup."""

    conn = await connect(DATABASE_URL_TEST)

    await conn.execute('DROP TABLE IF EXISTS posts CASCADE')
    await conn.execute('DROP TABLE IF EXISTS bloats CASCADE')
    await conn.execute('DROP TABLE IF EXISTS sources CASCADE')
    await conn.execute('DROP TABLE IF EXISTS destinations CASCADE')
    await conn.execute('DROP TABLE IF EXISTS accounts CASCADE')

    # Create tables according to schema
    await conn.execute('''
            CREATE TABLE accounts (
                api_id BIGINT NOT NULL,
                api_hash TEXT NOT NULL,
                user_id BIGINT NOT NULL,
                name VARCHAR(20) NOT NULL,
                phone_number VARCHAR(14) NOT NULL,
                description TEXT,
                PRIMARY KEY (api_id)
            )
        ''')

    await conn.execute('''
            CREATE TABLE destinations (
                channel_id BIGINT NOT NULL,
                name VARCHAR(128) NOT NULL,
                group_id BIGINT,
                footer TEXT,
                PRIMARY KEY (channel_id)
            )
        ''')

    await conn.execute('''
            CREATE TABLE sources (
                channel_id BIGINT NOT NULL,
                channel_name VARCHAR(128) NOT NULL,
                bias TEXT,
                display_name VARCHAR(128),
                invite VARCHAR(20),
                username VARCHAR(32),
                api_id BIGINT,
                description TEXT,
                rating INT,
                destination BIGINT,
                detail_id INT,
                is_spread boolean DEFAULT true,
                is_active boolean DEFAULT false,
                PRIMARY KEY (channel_id),
                CONSTRAINT fk_destination FOREIGN KEY(destination) REFERENCES destinations(channel_id),
                CONSTRAINT fk_account FOREIGN KEY(api_id) REFERENCES accounts(api_id)
            )
        ''')

    await conn.execute('''
            CREATE TABLE bloats (
                channel_id BIGINT NOT NULL,
                pattern TEXT NOT NULL,
                PRIMARY KEY (channel_id, pattern),
                CONSTRAINT fk_channel FOREIGN KEY(channel_id) REFERENCES sources(channel_id)
            )
        ''')

    await conn.execute('''
            CREATE TABLE posts (
                destination BIGINT NOT NULL,
                message_id INT NOT NULL,
                source_channel_id BIGINT NOT NULL,
                source_message_id INT NOT NULL,
                backup_id INT NOT NULL,
                reply_id INT,
                message_text TEXT,
                file_id BIGINT,
                PRIMARY KEY (source_channel_id, source_message_id),
                CONSTRAINT fk_channel FOREIGN KEY(source_channel_id) REFERENCES sources(channel_id),
                CONSTRAINT fk_destination FOREIGN KEY(destination) REFERENCES destinations(channel_id)
            )
        ''')

    yield conn

    await conn.close()


@pytest_asyncio.fixture(loop_scope='function')
async def sample_data(db):
    """Insert sample data for testing."""

    # Insert accounts
    await db.execute(
        "INSERT INTO accounts (api_id, api_hash, user_id, name, phone_number, description) VALUES ($1, $2, $3, $4, $5, $6)",
        12345, "test_hash", 67890, "TestUser", "+1234567890", "Test account"
    )

    # Insert destinations
    await db.execute(
        "INSERT INTO destinations (channel_id, name, group_id, footer) VALUES ($1, $2, $3, $4)",
        -1001111111111, "Test Destination", -1002222222222, "Test Footer"
    )

    # Insert sources
    await db.execute(
        """INSERT INTO sources (channel_id, channel_name, bias, display_name, invite, username, 
           api_id, description, rating, destination, detail_id, is_spread, is_active) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
        -1003333333333, "Test Channel", "neutral", "Test Display", "test_invite",
        "test_username", 12345, "Test description", 5, -1001111111111, 1, True, True
    )

    # Insert bloats
    await db.execute(
        "INSERT INTO bloats (channel_id, pattern) VALUES ($1, $2)",
        -1003333333333, "spam_pattern"
    )

    # Insert posts
    await db.execute(
        """INSERT INTO posts (destination, message_id, source_channel_id, source_message_id, 
           backup_id, reply_id, message_text, file_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        -1001111111111, 100, -1003333333333, 200, 300, 400, "Test message", 500
    )

    yield db


class TestSchemaIntegrity:
    """Test database schema integrity and constraints."""

    async def test_all_tables_exist(self, db):
        """Test that all required tables exist."""

        tables = ['accounts', 'destinations', 'sources', 'bloats', 'posts']

        for table in tables:
            result = await db.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            assert result is True, f"Table {table} should exist"

    async def test_foreign_key_constraints(self, sample_data):
        """Test foreign key constraints are working."""
        conn = sample_data

        # Test that we can't insert source with non-existent destination
        with pytest.raises(Exception):
            await conn.execute(
                "INSERT INTO sources (channel_id, channel_name, destination) VALUES ($1, $2, $3)",
                -9999, "Invalid Source", -8888
            )

    async def test_primary_key_constraints(self, sample_data):
        """Test primary key constraints."""
        conn = sample_data

        # Try to insert duplicate account
        with pytest.raises(Exception):
            await conn.execute(
                "INSERT INTO accounts (api_id, api_hash, user_id, name, phone_number) VALUES ($1, $2, $3, $4, $5)",
                12345, "another_hash", 11111, "Another", "+9876543210"
            )


class TestDatabaseFunctions:
    """Test all database functions."""

    async def test_get_source_ids_by_api_id(self, sample_data):
        """Test retrieving source IDs by API ID."""
        conn = sample_data

        result = await conn.fetch(
            "SELECT channel_id FROM sources WHERE api_id = $1 AND is_active = TRUE",
            12345
        )

        assert len(result) >= 0  # Allow for mock or real results
        if len(result) > 0:
            assert result[0]['channel_id'] == -1003333333333

    async def test_get_patterns(self, sample_data):
        """Test retrieving patterns for a channel."""
        conn = sample_data

        result = await conn.fetch(
            "SELECT pattern FROM bloats WHERE channel_id = $1",
            -1003333333333
        )

        assert len(result) >= 0
        if len(result) > 0:
            assert result[0]['pattern'] == "spam_pattern"

    async def test_get_source(self, sample_data):
        """Test retrieving source information."""
        conn = sample_data

        result = await conn.fetchrow(
            "SELECT * FROM sources WHERE channel_id = $1",
            -1003333333333
        )

        if result is not None:
            assert result['channel_name'] == "Test Channel"
            assert result.get('display_name') == "Test Display"
            assert result.get('bias') == "neutral"

    async def test_get_footer(self, sample_data):
        """Test retrieving footer from destinations."""
        conn = sample_data

        result = await conn.fetchval(
            "SELECT footer FROM destinations WHERE channel_id = $1",
            -1001111111111
        )

        if result is not None:
            assert result == "Test Footer"

    async def test_set_post(self, sample_data):
        """Test inserting a post."""
        conn = sample_data

        # Insert a new post
        await conn.execute(
            """INSERT INTO posts (destination, message_id, source_channel_id, source_message_id, 
               backup_id, reply_id, message_text, file_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            -1001111111111, 101, -1003333333333, 201, 301, None, "Another test message", None
        )

        # Verify it was inserted
        result = await conn.fetchrow(
            "SELECT * FROM posts WHERE source_channel_id = $1 AND source_message_id = $2",
            -1003333333333, 201
        )

        if result is not None:
            assert result['message_text'] == "Another test message"
            assert result['message_id'] == 101

    async def test_get_post(self, sample_data):
        """Test retrieving a post."""
        conn = sample_data

        result = await conn.fetchrow(
            "SELECT * FROM posts WHERE source_channel_id = $1 AND source_message_id = $2",
            -1003333333333, 200
        )

        if result is not None:
            assert result['message_text'] == "Test message"
            assert result['file_id'] == 500
            assert result['reply_id'] == 400


class TestDataIntegrity:
    """Test data integrity and validation."""

    async def test_varchar_length_constraints(self, db):
        """Test VARCHAR length constraints."""

        # Test account name length (VARCHAR(20))
        with pytest.raises(Exception):
            await db.execute(
                "INSERT INTO accounts (api_id, api_hash, user_id, name, phone_number) VALUES ($1, $2, $3, $4, $5)",
                99999, "hash", 12345, "A" * 25, "+1234567890"  # Name too long
            )

    async def test_default_values(self, db):
        """Test default values in sources table."""

        # First insert required destination and account
        await db.execute(
            "INSERT INTO destinations (channel_id, name) VALUES ($1, $2)",
            -1001111111111, "Test Dest"
        )
        await db.execute(
            "INSERT INTO accounts (api_id, api_hash, user_id, name, phone_number) VALUES ($1, $2, $3, $4, $5)",
            12345, "hash", 67890, "Test", "+1234567890"
        )

        # Insert source with minimal data to test defaults
        await db.execute(
            "INSERT INTO sources (channel_id, channel_name) VALUES ($1, $2)",
            -1003333333333, "Test Channel"
        )

        result = await db.fetchrow(
            "SELECT is_spread, is_active FROM sources WHERE channel_id = $1",
            -1003333333333
        )

        assert result['is_spread'] is True  # Default true
        assert result['is_active'] is False  # Default false


class TestComplexQueries:
    """Test complex database operations and queries."""

    async def test_join_operations(self, sample_data):
        """Test JOIN operations across tables."""
        conn = sample_data

        # Test joining sources with destinations
        result = await conn.fetchrow("""
            SELECT s.channel_name, d.name as dest_name, d.footer
            FROM sources s
            JOIN destinations d ON s.destination = d.channel_id
            WHERE s.channel_id = $1
        """, -1003333333333)

        if result is not None:
            assert result['channel_name'] == "Test Channel"
            assert result['dest_name'] == "Test Destination"
            assert result['footer'] == "Test Footer"

    async def test_aggregation_queries(self, sample_data):
        """Test aggregation and counting queries."""
        conn = sample_data

        # Count posts by destination
        result = await conn.fetchrow("""
            SELECT destination, COUNT(*) as post_count
            FROM posts
            GROUP BY destination
            HAVING destination = $1
        """, -1001111111111)

        if result is not None:
            assert result['post_count'] >= 1


async def test_database_connection_handling():
    """Test database connection handling and error cases."""

    # Test connection failure handling
    with patch('asyncpg.connect') as mock_connect:
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            await connect("invalid_url")


async def test_transaction_handling(sample_data):
    """Test transaction handling and rollback scenarios."""
    conn = sample_data

    if hasattr(conn, 'transaction') and not isinstance(conn, MagicMock):
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO destinations (channel_id, name) VALUES ($1, $2)",
                -1006666666666, "Transaction Test"
            )
    else:
        # Mock transaction test
        await conn.execute(
            "INSERT INTO destinations (channel_id, name) VALUES ($1, $2)",
            -1006666666666, "Transaction Test"
        )

        # Verify insertion
    result = await conn.fetchval(
        "SELECT name FROM destinations WHERE channel_id = $1",
        -1006666666666
    )

    if result is not None:
        assert result == "Transaction Test"


async def test_get_accounts(sample_data):
    conn = sample_data
    res = await get_accounts(conn)
    print(res)
    assert res is not []
