import NextAuthLib from "next-auth";
import { authOptions } from "./options";

const NextAuth = NextAuthLib.default ?? NextAuthLib;
const handler = NextAuth(authOptions);

export async function GET(req, context) {
  return handler(req, context);
}

export async function POST(req, context) {
  return handler(req, context);
}