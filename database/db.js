// db.js
import dotenv from "dotenv";
dotenv.config();

import { Sequelize } from "sequelize";

function makeSequelizeFromEnv() {
  // DATABASE_URL from env variables
  if (process.env.DATABASE_URL) {
    return new Sequelize(process.env.DATABASE_URL, {
      dialect: "postgres",
      logging: false,
      dialectOptions: {
        ssl: { require: true, rejectUnauthorized: false } // Supabase needs SSL
      }
    });
  }


}

export const sequelize = makeSequelizeFromEnv();

export async function connectAndSync() {
  await sequelize.authenticate();
  const { User } = await import("../models/User.js");
  await sequelize.sync();
  return { User };
}
