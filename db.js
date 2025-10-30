// db.js
import dotenv from "dotenv";
dotenv.config();

import { Sequelize } from "sequelize";

function makeSequelizeFromEnv() {
  // Prefer DATABASE_URL if present
  if (process.env.DATABASE_URL) {
    return new Sequelize(process.env.DATABASE_URL, {
      dialect: "postgres",
      logging: false,
      dialectOptions: {
        ssl: { require: true, rejectUnauthorized: false } // Supabase needs SSL
      }
    });
  }

  // Or discrete vars
  return new Sequelize(
    process.env.PGDATABASE,
    process.env.PGUSER,
    process.env.PGPASSWORD,
    {
      host: process.env.PGHOST,
      port: Number(process.env.PGPORT || 5432),
      dialect: "postgres",
      logging: false,
      dialectOptions: {
        ssl: { require: true, rejectUnauthorized: false }
      },
      pool: { max: 5, idle: 10000 } // small pool for class demos
    }
  );
}

export const sequelize = makeSequelizeFromEnv();

export async function connectAndSync() {
  await sequelize.authenticate();
  const { User } = await import("./models/User.js");
  await sequelize.sync();
  return { User };
}
