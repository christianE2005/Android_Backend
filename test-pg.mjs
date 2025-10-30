// test-pg.mjs
import "dotenv/config";
import pkg from "pg";
const { Client } = pkg;

const client = new Client({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});
await client.connect();
console.log((await client.query("select now() as now")).rows[0]);
await client.end();
