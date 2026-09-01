package Ejercicio_06;

import java.time.LocalDate;
import java.util.Arrays;

public class Main {
    public static void main(String[] args) {
        System.out.println("=== DEMO EJERCICIO 06: PARQUES NACIONALES ===\n");

        // 1. Crear Especies
        EspecieVegetal pino = new EspecieVegetal("Pinus halepensis", "Pino carrasco", true, "Primavera");
        EspecieAnimal lince = new EspecieAnimal("Lynx pardinus", "Lince ibérico", "Enero-Febrero", "Carnívora", Arrays.asList(pino));

        // 2. Crear Áreas y registrar especies
        Area area1 = new Area("Zona Norte - Los Alcornocales", 150.5);
        area1.registrarEspecie(pino, 5000);
        area1.registrarEspecie(lince, 45);

        // 3. Crear Personal
        Celador celador = new Celador("12345678A", "Juan Pérez", "Calle Falsa 123", "555-1234", 1800.0, "SS-987654", 1);
        Guarda guarda = new Guarda("87654321B", "Ana Gómez", "Av. Principal 456", "555-5678", 2100.0, "SS-123456", "Camioneta 4x4", "ABC-123", area1);
        
        Proyecto proyecto = new Proyecto("Conservación de Fauna", 50000.0, LocalDate.of(2026, 1, 1), LocalDate.of(2026, 12, 31));
        Investigador investigador = new Investigador("11223344C", "Dr. Carlos Ruiz", "Campus Univ.", "555-9988", 3200.0, "SS-555444", "Doctor en Biología", Arrays.asList(proyecto));

        // 4. Crear Parque Nacional
        ParqueNacional parque = new ParqueNacional(
                "Parque Nacional Doñana",
                LocalDate.of(1969, 10, 16),
                Arrays.asList(area1),
                Arrays.asList("Entrada Principal", "Entrada Sur"),
                Arrays.asList(new Alojamiento("Refugio Central", 50, "Alta")),
                Arrays.asList(celador, guarda, investigador)
        );

        // 5. Demostración de funcionalidades
        System.out.println("Parque Nacional: " + parque.getNombre() + " (Declarado en: " + parque.getFechaDeclaracionPN() + ")");
        System.out.println("Área registrada: " + area1.getNombre() + " (" + area1.getKm2() + " km2)");
        System.out.println(" - Especie Vegetal: " + pino.getNombreVulgar() + " (Floración en: " + pino.getPeriodoFloracion() + ")");
        System.out.println(" - Especie Animal: " + lince.getNombreVulgar() + " (Alimentación: " + lince.getTipoAlimentacion() + ")");
        
        System.out.println("\n--- ACCIONES DEL PERSONAL ---");
        Visitante visitante = new Visitante("99887766Z", "Sofía Torres", "Calle Sol 99", "Turista");
        celador.registrarVisita(visitante);
        guarda.recorrerArea();
        System.out.println("Investigador: " + investigador.getNombre() + " (" + investigador.getTitulacion() + ") lidera proyecto: " + proyecto.getNombre());

        System.out.println("\n=== DEMO EJERCICIO 06 COMPLETADA EXITOSAMENTE ===");
    }
}
