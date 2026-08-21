package Ejercicio_09;

import java.time.LocalDate;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        System.out.println("=== DEMO EJERCICIO 9: SISTEMA DE MUSEO ==-\n");

        // 1. Crear el Museo (Composición de colección y exposiciones)
        Museo museo = new Museo("Museo Nacional de Bellas Artes");

        // 2. Crear Artistas
        Artista daVinci = new Artista(
                "Leonardo da Vinci",
                LocalDate.of(1452, 4, 15),
                LocalDate.of(1519, 5, 2),
                "Italia",
                "Renacimiento",
                "Sfumato",
                "Genio universal del Renacimiento."
        );

        Artista rodin = new Artista(
                "Auguste Rodin",
                LocalDate.of(1840, 11, 12),
                LocalDate.of(1917, 11, 17),
                "Francia",
                "Impresionismo/Realismo",
                "Escultura figurativa",
                "Padre de la escultura moderna."
        );

        // 3. Crear Colecciones Externas (para obras en préstamo)
        ColeccionExterna coleccionLouvre = new ColeccionExterna(
                "Museo del Louvre",
                "Museo Estatal",
                "Colección de arte europeo",
                "París, Francia",
                "+33 1 40 20 50 50",
                "Jean Dupont"
        );
        museo.agregarColeccionExterna(coleccionLouvre);

        // 4. Crear Estados de Tenencia
        // Permanente (adquirido, coste, en exposición o almacén)
        Permanente tenenciaPermanente1 = new Permanente(
                LocalDate.of(1950, 6, 12),
                1500000.0,
                true // En exposición
        );

        // Préstamo (con fecha de recepción, devolución y colección origen)
        Prestamo tenenciaPrestamo1 = new Prestamo(
                LocalDate.of(2025, 1, 10),
                LocalDate.of(2026, 1, 10),
                coleccionLouvre
        );

        // 5. Crear Objetos de Arte (Pintura, Escultura, OtroObjeto)
        // Pintura permanente
        Pintura monaLisaCopy = new Pintura(
                "PIN-001",
                "Retrato Renacentista",
                "Estudio inspirado en la obra clásica",
                1503,
                "Italia",
                "Europea",
                "Renacimiento",
                daVinci,
                tenenciaPermanente1,
                "Óleo",
                "Lienzo",
                "Retrato"
        );

        // Escultura en préstamo
        Escultura pensador = new Escultura(
                "ESC-001",
                "El Pensador (Réplica Autorizada)",
                "Escultura de bronce fundido",
                1904,
                "Francia",
                "Occidental",
                "Moderna",
                rodin,
                tenenciaPrestamo1,
                "Bronce",
                1.85,
                200.0,
                "Realismo"
        );

        // Otro objeto de arte (permanente)
        Permanente tenenciaPermanente2 = new Permanente(
                LocalDate.of(1980, 3, 15),
                85000.0,
                false // En almacén
        );
        OtroObjeto ceramicaMaya = new OtroObjeto(
                "OTR-001",
                "Vasija Ceremonial Policromada",
                "Vasija ritual con glifos",
                null, // anioCreacion desconocido
                "México",
                "Maya",
                "Clásico Tardío",
                null, // Artista anónimo
                tenenciaPermanente2,
                "Cerámica ritual"
        );

        // Agregar objetos al Museo (Composición Museo — ObjetoDeArte)
        museo.agregarObjeto(monaLisaCopy);
        museo.agregarObjeto(pensador);
        museo.agregarObjeto(ceramicaMaya);

        // 6. Crear Exposiciones y exhibir obras (Agregación Exposicion — ObjetoDeArte)
        Exposicion expoRenacimiento = new Exposicion(
                "Maestros del Renacimiento y Modernismo",
                LocalDate.of(2026, 3, 1),
                LocalDate.of(2026, 6, 30)
        );
        expoRenacimiento.agregarObjeto(monaLisaCopy);
        expoRenacimiento.agregarObjeto(pensador); // Exhibe obras de colección y de préstamo

        museo.agregarExposicion(expoRenacimiento);

        // 7. Mostrar resumen general que valida todas las relaciones
        museo.mostrarResumen();

        System.out.println("\n--- DEMO EJERCICIO 9 COMPLETADA EXITOSAMENTE ---");
    }
}
