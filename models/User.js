import { DataTypes } from "sequelize";
import { sequelize } from "../database/db.js";

export const User = sequelize.define(
  "User",
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true
    },
    email: {
      type: DataTypes.STRING,
      unique: true,
      allowNull: false,
      validate: { isEmail: true }
    },
    is_admin: {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: false
    }
  },
  {
    tableName: "users",
    schema: "public",
    timestamps: true,             // adds createdAt, updatedAt
    createdAt: "created_at",
    updatedAt: "updated_at"
  }
);
