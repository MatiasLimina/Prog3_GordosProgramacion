package Ejercicio_10;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        System.out.println("=== DEMO EJERCICIO 10: JUEGOS OLÍMPICOS ==-\n");

        // 1. Crear Deportes
        Deporte atletismo = new Deporte("Atletismo");
        Deporte natacion = new Deporte("Natación");
        Deporte futbol = new Deporte("Fútbol");

        // 2. Crear Áreas Designadas (Asociación con Deporte)
        AreaDesignada areaPista = new AreaDesignada("Centro (Pista principal)", atletismo);
        AreaDesignada areaTribuna = new AreaDesignada("Esquina N-E", futbol);
        AreaDesignada areaPiscina = new AreaDesignada("Zona Norte", natacion);

        // 3. Crear Complejos Deportivos (Herencia y Composición de Áreas)
        // Complejo único deporte
        ComplejoUnicoDeporte estadioAtletismo = new ComplejoUnicoDeporte(
                "Sector A - Parque Olímpico",
                "Carlos Mendoza",
                45000.0,
                Arrays.asList(areaPista),
                atletismo
        );

        // Polideportivo (multideporte)
        Polideportivo polideportivoCentral = new Polideportivo(
                "Sector B - Ciudad Deportiva",
                "Laura Gómez",
                80000.0,
                Arrays.asList(areaTribuna, areaPiscina),
                Arrays.asList(futbol, natacion)
        );

        // 4. Crear Sede Olímpica (Composición Sede — Complejos)
        SedeOlimpica sedeOlimpica = new SedeOlimpica(
                125000000.0,
                Arrays.asList(estadioAtletismo, polideportivoCentral)
        );

        // 5. Crear Comisarios
        Comisario comisario1 = new Comisario("COM-001", "Roberto Sánchez");
        Comisario comisario2 = new Comisario("COM-002", "María Elena Ross");

        // 6. Crear Eventos (Asociación Complejo — Evento y N:M Evento — Comisario)
        Evento carrera100m = new Evento(
                LocalDate.of(2026, 7, 15),
                120, // 120 minutos
                8,   // participantes
                2,   // comisarios requeridos
                Arrays.asList("Pértigas", "Bloques de salida"),
                estadioAtletismo
        );
        carrera100m.agregarComisario(comisario1);
        carrera100m.agregarComisario(comisario2);

        Evento partidoFutbol = new Evento(
                LocalDate.of(2026, 7, 16),
                90,  // 90 minutos
                22,  // participantes
                4,   // comisarios requeridos
                Arrays.asList("Porterías", "Balones oficiales"),
                polideportivoCentral
        );
        partidoFutbol.agregarComisario(comisario1); // Comisario 1 en múltiples eventos (N:M)

        // 7. Mostrar Resumen de la Sede Olímpica y sus relaciones
        System.out.println("--- INFORMACIÓN DE LA SEDE OLÍMPICA ---");
        System.out.println("Presupuesto Aproximado: $" + sedeOlimpica.getPresupuestoAproximado());
        System.out.println("Número de Complejos (derivado/actual): " + sedeOlimpica.getNumeroComplejos());
        
        for (ComplejoDeportivo complejo : sedeOlimpica.getComplejos()) {
            System.out.println("\nComplejo: " + complejo.getClass().getSimpleName());
            System.out.println(" - Localización: " + complejo.getLocalizacion());
            System.out.println(" - Jefe de Organización: " + complejo.getJefeOrganizacion());
            System.out.println(" - Área Ocupada: " + complejo.getAreaOcupada() + " m²");
            
            System.out.println(" - Áreas Designadas:");
            for (AreaDesignada area : complejo.getAreas()) {
                System.out.println("   * Situación: " + area.getIndicadorSituacion() + " (Deporte: " + area.getDeporte().getNombre() + ")");
            }

            if (complejo instanceof ComplejoUnicoDeporte) {
                System.out.println(" - Deporte Exclusivo: " + ((ComplejoUnicoDeporte) complejo).getDeporteExclusivo().getNombre());
            } else if (complejo instanceof Polideportivo) {
                System.out.print(" - Deportes Admitidos: ");
                Polideportivo poli = (Polideportivo) complejo;
                for (int i = 0; i < poli.getDeportesAdmitidos().size(); i++) {
                    System.out.print(poli.getDeportesAdmitidos().get(i).getNombre() + (i < poli.getDeportesAdmitidos().size() - 1 ? ", " : ""));
                }
                System.out.println();
            }

            System.out.println(" - Eventos Celebrados en este Complejo (" + complejo.getEventos().size() + "):");
            for (Evento evento : complejo.getEventos()) {
                System.out.println("   * Fecha: " + evento.getFecha() + ", Duración: " + evento.getDuracionMinutos() + " mins, Participantes: " + evento.getNumeroParticipantes());
                System.out.println("     Material: " + evento.getMaterialNecesario());
                System.out.print("     Comisarios Asignados (" + evento.getComisarios().size() + "): ");
                for (Comisario c : evento.getComisarios()) {
                    System.out.print(c.getNombre() + " ");
                }
                System.out.println();
            }
        }

        System.out.println("\n--- VERIFICACIÓN DE ASOCIACIÓN N:M (Comisarios) ---");
        System.out.println("Comisario 1 (" + comisario1.getNombre() + ") participa en " + comisario1.getEventos().size() + " evento(s):");
        for (Evento ev : comisario1.getEventos()) {
            System.out.println(" - Evento en " + ev.getComplejo().getLocalizacion() + " (" + ev.getFecha() + ")");
        }

        System.out.println("\n--- DEMO EJERCICIO 10 COMPLETADA EXITOSAMENTE ---");
    }
}
