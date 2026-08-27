package Ejercicio_06;

import java.sql.Time;
import java.util.Arrays;
import java.util.Date;

public class Main {
    public static void main(String[] args) {
        System.out.println("=== DEMO EJERCICIO 06: PARQUES NACIONALES ==-\n");

        // 1. Comunidad Autónoma
        ComunidadAutonoma caAndalucia = new ComunidadAutonoma("Andalucía", "Consejería de Medio Ambiente");

        // 2. Parque Nacional
        ParqueNacional pnMunana = new ParqueNacional("Parque Nacional de Doñana", new Date());
        pnMunana.agregarComunidadAutonoma(caAndalucia);

        // 3. Áreas (Composición)
        Area areaNorte = new Area("Marismas del Norte", 150.5);
        Area areaSur = new Area("Dunas Litorales", 95.0);
        pnMunana.agregarArea(areaNorte);
        pnMunana.agregarArea(areaSur);

        // 4. Entradas (Composición)
        Entrada entrada1 = new Entrada(1);
        Entrada entrada2 = new Entrada(2);
        pnMunana.agregarEntrada(entrada1);
        pnMunana.agregarEntrada(entrada2);

        // 5. Alojamientos (Composición)
        Alojamiento hotelParque = new Alojamiento("Hotel Doñana Park", 120, "4 Estrellas");
        pnMunana.agregarAlojamiento(hotelParque);

        // 6. Especies y Cadena Trófica
        EspecieVegetal pino = new EspecieVegetal("Pinus pinea", "Pino Piñonero", true, "Primavera");
        Herbivoro ciervo = new Herbivoro("Cervus elaphus", "Ciervo Ibérico", "Otoño");
        ciervo.agregarAlimento(pino); // Animal se alimenta de vegetal

        Carnivoro lince = new Carnivoro("Lynx pardinus", "Lince Ibérico", "Invierno");
        lince.agregarAlimento(ciervo); // Lince se alimenta de ciervo

        // Registrar censos en área
        areaNorte.registrarEspecie(pino, 5000);
        areaNorte.registrarEspecie(ciervo, 350);
        areaSur.registrarEspecie(lince, 25);

        // 7. Personal y Roles (Guarda, Celador, Investigador)
        Vehiculo vehiculo1 = new Vehiculo("Todo Terreno 4x4", "ABC-1234");
        Guarda guarda1 = new Guarda("12345678A", "Esteban Guarda", "Calle Bosque 10", "+34600111222", 2200.0, "SS-001", areaNorte, vehiculo1);
        pnMunana.agregarPersonal(guarda1);

        Celador celador1 = new Celador("87654321B", "Lucía Celador", "Calle Entrada 5", "+34600333444", 1800.0, "SS-002", entrada1);
        pnMunana.agregarPersonal(celador1);

        Investigador investigador1 = new Investigador("45612378C", "Dr. Manuel Investigador", "Univ. Biología", "+34600555666", 3100.0, "SS-003", "Doctor en Ecología");
        pnMunana.agregarPersonal(investigador1);

        // 8. Proyecto de Investigación y Especies Investigadas
        ProyectoInvestigacion proyectoLince = new ProyectoInvestigacion("Monitoreo Felino 2026", 150000.0, new Date(), new Date());
        proyectoLince.agregarInvestigador(investigador1);
        proyectoLince.agregarEspecieInvestigada(lince);

        // 9. Visitantes, Estadías y Excursiones
        Visitante visitante1 = new Visitante("99887766Z", "Roberto Viajero", "Gran Vía 50", "Fotógrafo");
        Estadia estadia1 = new Estadia("Hab 204", new Date(), new Date(), visitante1, hotelParque);

        Excursion excursion1 = new Excursion("EXC-001", new Date(), new Time(10, 0, 0));
        hotelParque.agregarExcursion(excursion1);
        visitante1.inscribirExcursion(excursion1);

        // 10. Registro de Visita en Entrada por Celador
        celador1.registrarVisita(visitante1, new Date());

        // 11. Imprimir Resumen Demo
        System.out.println("Parque Nacional: " + pnMunana.getNombre());
        System.out.println("Comunidades Autónomas: " + caAndalucia.getNombre() + " (Organismo: " + caAndalucia.getOrganismoResponsable() + ")");
        System.out.println("Áreas registradas: " + pnMunana.getAreas().size());
        for (Area a : pnMunana.getAreas()) {
            System.out.println(" - " + a.getNombre() + " (" + a.getExtensionKm2() + " km²), Guardas asignados: " + a.getGuardas().size());
            for (CensoEspecie ce : a.getCensoEspecies()) {
                System.out.println("   * Especie: " + ce.getEspecie().getNombreVulgar() + " (Individuos: " + ce.getNumeroIndividuos() + ")");
            }
        }
        System.out.println("Entradas y Celadores: Entrada #" + entrada1.getNumero() + " asignada a " + celador1.getNombre());
        System.out.println("Visitas registradas en entrada: " + entrada1.getRegistrosVisita().size());
        System.out.println("Alojamientos: " + hotelParque.getNombre() + " (Capacidad: " + hotelParque.getCapacidad() + ")");
        System.out.println("Visitantes en excursión: " + excursion1.getVisitantes().size() + " (" + visitante1.getNombre() + ")");
        System.out.println("Investigador: " + investigador1.getNombre() + " en proyecto '" + proyectoLince.getNombre() + "'");

        System.out.println("\n--- DEMO EJERCICIO 06 COMPLETADA EXITOSAMENTE ---");
    }
}
