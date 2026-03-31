package auth

import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm
import java.util.Date

object JwtConfig {
    private val secret = System.getenv("JWT_SECRET") ?: "dev-secret-change-me"
    private const val issuer = "perfx-backend"
    private const val audience = "perfx-frontend"
    private const val validityMs = 1000L * 60L * 60L * 24L // 24h

    private val algorithm = Algorithm.HMAC256(secret)

    fun makeToken(userId: String, email: String): String =
        JWT.create()
            .withIssuer(issuer)
            .withAudience(audience)
            .withSubject(userId)
            .withClaim("email", email)
            .withExpiresAt(Date(System.currentTimeMillis() + validityMs))
            .sign(algorithm)

    fun verifier() = JWT
        .require(algorithm)
        .withIssuer(issuer)
        .withAudience(audience)
        .build()

    const val realm = "perfx"
}