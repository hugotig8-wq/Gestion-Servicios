// ./app/api/auth/[...nextauth]/options.js
import NextAuthCredentials from "next-auth/providers/credentials";
const CredentialsProvider = NextAuthCredentials.default ?? NextAuthCredentials;

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Contraseña", type: "password" }
      },
      async authorize(credentials) {
        const { query } = await import("@/lib/db");
        const res = await query('SELECT * FROM usuarios WHERE email = $1', [credentials.email]);
        const user = res.rows[0];

        if (user && user.password_hash === credentials.password) {
          return { id: user.id, name: user.nombre, email: user.email };
        }
        return null;
      }
    })
  ],
  pages: {
    signIn: '/', // Usa tu propia página de login
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) token.id = user.id;
      return token;
    },
    async session({ session, token }) {
      if (session.user) session.user.id = token.id;
      return session;
    }
  },
  secret: process.env.NEXTAUTH_SECRET,
  session: { strategy: "jwt" }
};