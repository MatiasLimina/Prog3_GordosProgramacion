package Ejercicio_08;

import java.time.LocalDate;

public class Main {
    public static void main(String[] args) {
        System.out.println("=== DEMO EJERCICIO 08: AERÓDROMO ===\n");

        // 1. Crear Tipo de Avión
        TipoAvion tipo = new TipoAvion("Boeing 737", 180, 41415.0);

        // 2. Crear Hangar
        Hangar hangar = new Hangar(1, 3, "Zona Oeste");

        // 3. Crear Propietario
        Propietario propietario = new Propietario("20-33333333-3", "Juan Pérez", "Av. Libertador 1000", "555-1234");

        // 4. Crear Avión
        Avion avion = new Avion("LV-ABC", tipo, hangar, propietario, LocalDate.of(2023, 5, 12));

        // 5. Crear Personal
        Piloto piloto = new Piloto("20-11111111-1", "Carlos Gómez", "Calle 5 N° 200", "555-5678", "LIC-5544", "Ninguna");
        Mecanico mecanico = new Mecanico("20-22222222-2", "Ana Torres", "Ruta 2 Km 40", "555-9988", 3500.0, "Rotativo");

        piloto.agregarTipoAutorizado(tipo);
        mecanico.agregarTipoMantenimiento(tipo);

        // 6. Registrar Servicios
        Servicio servicio1 = new Servicio(LocalDate.of(2024, 1, 10), 5.0, "Revision de motores", mecanico);
        avion.agregarServicio(servicio1);

        System.out.println("Avión Matrícula: " + avion.getMatricula());
        System.out.println("Propietario: " + avion.getPropietarioActual().getNombre());
        System.out.println("Hangar: N° " + avion.getHangarActual().getNumero() + " (" + avion.getHangarActual().getUbicacion() + ")");
        System.out.println("Servicios registrados: " + avion.getHistorialServicios().size());

        // 7. Prueba de excepción (mismo servicio en misma fecha y tipo de trabajo)
        try {
            Servicio servicioDuplicado = new Servicio(LocalDate.of(2024, 1, 10), 2.0, "Revision de motores", mecanico);
            avion.agregarServicio(servicioDuplicado);
        } catch (IllegalArgumentException e) {
            System.out.println("\n[Excepción capturada con éxito]: " + e.getMessage());
        }

        System.out.println("\n=== DEMO EJERCICIO 08 COMPLETADA EXITOSAMENTE ===");
    }
}
