package Ejercicio_07;

import java.time.LocalDate;

public class Main {
    public static void main(String[] args) {
        System.out.println("=== DEMO EJERCICIO 07: CAMPEONATO DE ESQUÍ ===\n");

        // 1. Crear el Campeonato (Contenedor fuerte)
        Campeonato campeonato = new Campeonato();

        // 2. Crear Federaciones
        Federacion fedAndina = new Federacion("Federación Andina de Esquí");
        Federacion fedPatagonica = new Federacion("Federación Patagónica de Esquí");

        // 3. Crear Estación de Esquí (Administrada por una o varias federaciones)
        Estacion cerroBayo = new Estacion("EST-01", "Cerro Bayo", "Ruta 66 km 4", "0294-449200", 35.0f);
        cerroBayo.agregarPersonaContacto("Juan Administrador");
        
        // Asociar Estación a Federación (N:M)
        fedAndina.agregarEstacion(cerroBayo);
        fedPatagonica.agregarEstacion(cerroBayo);

        // 4. Crear Pistas en la Estación (Composición fuerte) y Subpistas (Auto-composición)
        Pista pistaPrincipal = cerroBayo.crearPista(5.5f, "Azul");
        Pista subpista1 = cerroBayo.crearPista(2.0f, "Verde");
        Pista subpista2 = cerroBayo.crearPista(3.5f, "Roja");
        pistaPrincipal.agregarSubpista(subpista1);
        pistaPrincipal.agregarSubpista(subpista2);

        System.out.println("Estación: " + cerroBayo.getNombre() + " | Total Pistas: " + cerroBayo.getNumeroPistas());
        System.out.println("Federaciones administradoras: " + cerroBayo.getFederacionesAdmin());

        // 5. Crear Esquiadores (Obligatoriamente asociados a una Federación)
        Esquiador esquiador1 = new Esquiador("35111222", "Carlos Gómez", LocalDate.of(1995, 5, 12), fedAndina);
        Esquiador esquiador2 = new Esquiador("36222333", "Lucía Fernández", LocalDate.of(1998, 8, 21), fedAndina);
        Esquiador esquiador3 = new Esquiador("34333444", "Mateo Rossi", LocalDate.of(1992, 2, 15), fedPatagonica);

        System.out.println("\n--- FEDERADOS ---");
        System.out.println("Federación: " + fedAndina.getNombre() + " | Nº de Federados: " + fedAndina.getNumeroFederados());
        System.out.println("Edad de " + esquiador1.getNombre() + ": " + esquiador1.getEdad() + " años.");

        // 6. Crear Equipo y agregar Esquiadores (Agregación)
        Equipo equipoAndino = new Equipo("EQ-A", "Marcos Entrenador");
        equipoAndino.agregarEsquiador(esquiador1);
        equipoAndino.agregarEsquiador(esquiador2);

        System.out.println("Equipo " + equipoAndino.getCodigo() + " | Cantidad de esquiadores: " + equipoAndino.getCantidadEsquiadores());

        // 7. Crear Pruebas en el Campeonato
        Prueba slalomGigante = new Prueba("Slalom Gigante de Invierno", "Slalom", campeonato, cerroBayo);
        slalomGigante.agregarFechaPrevista(LocalDate.of(2026, 7, 10));

        Prueba fondoEquipos = new Prueba("Gran Fondo Patagónico", "Fondo", campeonato, cerroBayo);
        fondoEquipos.agregarFechaPrevista(LocalDate.of(2026, 7, 12));

        // 8. Inscribir Participantes (Polimorfismo: Esquiador individual o Equipo)
        Inscripcion inscripcionIndividual = slalomGigante.inscribirParticipante(esquiador3, 101);
        inscripcionIndividual.agregarFechaParticipacion(LocalDate.of(2026, 7, 10));
        inscripcionIndividual.setTiempoEmpleado(54.2f);
        inscripcionIndividual.setPosicionObtenida(1);

        slalomGigante.setVencedor(esquiador3.getNombre());
        slalomGigante.setTiempoEmpleadoVencedor(54.2f);

        Inscripcion inscripcionEquipo = fondoEquipos.inscribirParticipante(equipoAndino, 201);
        inscripcionEquipo.agregarFechaParticipacion(LocalDate.of(2026, 7, 12));
        inscripcionEquipo.setTiempoEmpleado(125.4f);
        inscripcionEquipo.setPosicionObtenida(1);

        fondoEquipos.setVencedor("Equipo " + equipoAndino.getCodigo());
        fondoEquipos.setTiempoEmpleadoVencedor(125.4f);

        System.out.println("\n--- RESULTADOS DE PRUEBAS ---");
        System.out.println("Prueba: " + slalomGigante.getNombre() + " | Vencedor: " + slalomGigante.getVencedor() + " (Código inscripción: " + inscripcionIndividual.getCodigoInscripcion() + ")");
        System.out.println("Prueba: " + fondoEquipos.getNombre() + " | Vencedor: " + fondoEquipos.getVencedor() + " (Código inscripción: " + inscripcionEquipo.getCodigoInscripcion() + ")");

        System.out.println("\n=== DEMO EJERCICIO 07 COMPLETADA EXITOSAMENTE ===");
    }
}
